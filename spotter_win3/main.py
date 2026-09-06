"""UI/poll loop entry point (Tech item 3). A daemon worker thread owns the
cluster socket entirely; the UI thread only touches its queue and
send_command() — filter-setup commands dispatch off the UI thread so they
never block it (Tech item 4). The main loop drains the queue on a ~200ms
poll (Tech item 1).
"""

from __future__ import annotations

import queue
import sys
import threading
import time
import tkinter as tk

if sys.platform == "win32":
    # Without this, Windows DPI-virtualizes the process: Tk's own geometry
    # (winfo_width/rootx/etc.) is reported in unscaled logical pixels while
    # a raw screen capture (PIL.ImageGrab) reads true physical pixels, so
    # the two disagree about window size/position — this must run before
    # any Tk() is created.
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass

from spotter_win3 import config as config_module
from spotter_win3.bandmap import BandScope
from spotter_win3.cluster import ClusterConnection, Spot, parse_spot_line
from spotter_win3.cluster_profiles import (
    DEFAULT_PROFILE,
    PROFILES,
    ClusterProfile,
    band_for_freq_mhz,
)
from spotter_win3.controls import ControlsPanel
from spotter_win3.filters import DedupCache, is_cw_mode
from spotter_win3.pota import PotaSpot, PotaWorker
from spotter_win3.scope_utils import in_window
from spotter_win3.spot_store import SpotStore

POLL_INTERVAL_MS = 200
RECONNECT_BACKOFF_SECONDS = 5.0


class ClusterWorker:
    """Owns the socket on its own daemon thread. The UI thread only ever
    reads self.incoming and calls set_filter_commands()/stop().

    Auto-reconnects with a fixed backoff on connection loss (previously
    it exited permanently, leaving status red until the operator hit
    Clear — see improvement-queue.md item 3). The active filter commands
    are remembered and resent automatically after every reconnect.
    """

    def __init__(self, profile: ClusterProfile, callsign: str) -> None:
        self.profile = profile
        self.callsign = callsign
        self.incoming: queue.Queue = queue.Queue()
        self._outgoing: queue.Queue = queue.Queue()
        self._current_commands: list[str] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def set_filter_commands(self, commands: list[str]) -> None:
        """Replaces the active filter commands. Sent now (if connected)
        and automatically resent after any future reconnect."""
        self._current_commands = list(commands)
        for command in commands:
            self._outgoing.put(command)

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        host, port = self.profile.hosts[0]
        while not self._stop.is_set():
            conn = ClusterConnection(host, port, self.callsign)
            try:
                conn.connect()
                self.incoming.put(("status", True))
                for command in self._current_commands:
                    conn.send(command)
                while not self._stop.is_set():
                    while not self._outgoing.empty():
                        conn.send(self._outgoing.get_nowait())
                    for line in conn.read_lines(timeout=0.5):
                        spot = parse_spot_line(line)
                        if spot:
                            self.incoming.put(("spot", spot))
            except OSError:
                self.incoming.put(("status", False))
            finally:
                conn.close()
            if not self._stop.is_set():
                self._stop.wait(RECONNECT_BACKOFF_SECONDS)


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.cfg = config_module.load()
        self.profile: ClusterProfile = PROFILES.get(self.cfg.cluster_profile, DEFAULT_PROFILE)
        self.store = SpotStore()
        self.dedup = DedupCache()
        self._connected = False
        self._last_pota_poll: float | None = None

        root.title("spotter-win3")
        # 540x1305 matches the reference screenshot's aspect ratio (492x1189,
        # ratio 0.414) rather than an arbitrary size — width is padded a bit
        # over the reference's 492 to fit the added Server control and this
        # platform's font metrics without reintroducing the Task 3 clipping bug.
        root.geometry("540x1305+0+0")
        tk.Label(root, text="RBN & POTA Spotter", font=("TkDefaultFont", 16, "bold")).pack(
            pady=(8, 4)
        )

        # Leader line at exactly 90% width, centered (spec item 2) — place()
        # with relwidth keeps this exact regardless of window resizing,
        # unlike a fixed pixel padx.
        leader_container = tk.Frame(root, height=1)
        leader_container.pack(fill=tk.X, pady=4)
        tk.Frame(leader_container, height=1, bg="gray").place(
            relx=0.5, rely=0, relwidth=0.9, anchor="n"
        )

        body = tk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True)

        # Pack the fixed-width side first (controls), then let the scope
        # expand into whatever's left — packing expand=True first claims
        # the whole cavity before the other side gets a reserved slot.
        self.controls = ControlsPanel(
            body,
            on_set_band=self._on_set_band,
            on_bandwidth_change=self._on_bandwidth_change,
            on_window_change=self._on_window_change,
            on_tier_change=self._on_tier_change,
            on_clear=self._on_clear,
            on_server_change=self._on_server_change,
            initial_freq_mhz=self.cfg.center_freq_mhz,
            initial_bandwidth_khz=self.cfg.bandwidth_khz,
            initial_window_min=self.cfg.window_minutes,
            initial_tier=self.cfg.spotter_tier,
            cluster_name=self.profile.name,
            cluster_options=list(PROFILES.keys()),
        )
        self.controls.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        scope_column = tk.Frame(body)
        scope_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Packed to the same left/right edges as each lane's own content
        # (BandScope's cluster lane sits near x=0.08, POTA near x=0.92) so
        # each header actually sits above its lane, not just near it.
        headers = tk.Frame(scope_column)
        headers.pack(fill=tk.X, padx=(8, 8))
        tk.Label(headers, text="RBN", font=("TkDefaultFont", 10, "bold")).pack(
            side=tk.LEFT, anchor="w"
        )
        tk.Label(headers, text="POTA", font=("TkDefaultFont", 10, "bold")).pack(
            side=tk.RIGHT, anchor="e"
        )

        self.scope = BandScope(scope_column)
        self.scope.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.worker: ClusterWorker | None = None
        self._start_worker()

        # POTA polls independently of the cluster connection/Clear cycle —
        # it has no persistent connection to reconnect (spec item 8).
        self.pota_worker = PotaWorker()
        self.pota_worker.start()

        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _start_worker(self) -> None:
        self.worker = ClusterWorker(self.profile, self.cfg.operator_callsign or "N0CALL")
        self.worker.start()
        self.worker.set_filter_commands(self.profile.filter_commands(self.cfg.center_freq_mhz))

    def _poll(self) -> None:
        assert self.worker is not None
        try:
            while True:
                kind, payload = self.worker.incoming.get_nowait()
                if kind == "status":
                    self._connected = payload
                elif kind == "spot":
                    self._handle_spot(payload)
        except queue.Empty:
            pass

        try:
            while True:
                kind, payload = self.pota_worker.incoming.get_nowait()
                if kind == "poll_attempt":
                    self._last_pota_poll = payload
                elif kind == "spot":
                    self._handle_pota_spot(payload)
        except queue.Empty:
            pass

        self.store.prune(self.cfg.window_minutes * 60)
        self.scope.render(
            self.store.spots_for_feed("cluster"),
            self.store.spots_for_feed("pota"),
            self.cfg.center_freq_mhz * 1000,
            self.cfg.bandwidth_khz,
            self.cfg.window_minutes,
        )
        pota_age = (
            time.monotonic() - self._last_pota_poll
            if self._last_pota_poll is not None
            else None
        )
        center_khz = self.cfg.center_freq_mhz * 1000
        rbn_shown = sum(
            1
            for s in self.store.spots_for_feed("cluster")
            if in_window(s.freq_khz, center_khz, self.cfg.bandwidth_khz)
        )
        pota_shown = sum(
            1
            for s in self.store.spots_for_feed("pota")
            if in_window(s.freq_khz, center_khz, self.cfg.bandwidth_khz)
        )
        self.controls.set_status(self._connected, self.profile.name, pota_age, rbn_shown, pota_shown)
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _handle_spot(self, spot: Spot) -> None:
        try:
            band = band_for_freq_mhz(spot.freq_khz / 1000)
        except ValueError:
            return
        # Client-side authoritative fallback for profiles with no verified
        # server-side mode filter (spec item 7) — currently only W4MYA.
        if not self.profile.cw_trustworthy and not is_cw_mode(spot):
            return
        if self.dedup.is_duplicate(spot.dx_call, band):
            return
        self.store.upsert(
            spot.dx_call, band, "cluster", spot.freq_khz, spot.spotter, spot.comment
        )

    def _handle_pota_spot(self, spot: PotaSpot) -> None:
        try:
            band = band_for_freq_mhz(spot.freq_khz / 1000)
        except ValueError:
            return
        # No dedup for POTA spots (spec item 8).
        self.store.upsert(
            spot.dx_call, band, "pota", spot.freq_khz, spot.spotter, spot.comment
        )

    def _on_set_band(self, freq_mhz: float) -> str | None:
        try:
            commands = self.profile.filter_commands(freq_mhz)
        except ValueError:
            return f"{freq_mhz} MHz is not in a known amateur band"
        self.cfg.center_freq_mhz = freq_mhz
        config_module.save(self.cfg)
        assert self.worker is not None
        self.worker.set_filter_commands(commands)
        return None

    def _on_bandwidth_change(self, bandwidth_khz: int) -> None:
        self.cfg.bandwidth_khz = bandwidth_khz
        config_module.save(self.cfg)

    def _on_window_change(self, window_min: int) -> None:
        self.cfg.window_minutes = window_min
        config_module.save(self.cfg)

    def _on_tier_change(self, tier: str) -> None:
        self.cfg.spotter_tier = tier
        config_module.save(self.cfg)

    def _on_clear(self) -> None:
        self.store = SpotStore()
        self.dedup = DedupCache()
        self._connected = False
        if self.worker:
            self.worker.stop()
        self._start_worker()

    def _on_server_change(self, profile_name: str) -> None:
        profile = PROFILES.get(profile_name)
        if profile is None or profile is self.profile:
            return
        self.profile = profile
        self.cfg.cluster_profile = profile.name
        config_module.save(self.cfg)
        self.store = SpotStore()
        # Dedup state must reset too, not just the store — otherwise a
        # popular call+band already seen on the previous server within
        # the last 2 minutes silently suppresses it as a "duplicate" on
        # the new server, even though it's a genuinely new arrival from a
        # different feed. Root cause of the operator's "zero spots for 5
        # minutes on W4MYA" report — the cluster/filter/worker were all
        # confirmed working live; this was the only layer left unreset.
        self.dedup = DedupCache()
        self._connected = False
        if self.worker:
            self.worker.stop()
        self._start_worker()


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
