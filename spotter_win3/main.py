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
from spotter_win3.cluster_profiles import NC7J, ClusterProfile, band_for_freq_mhz
from spotter_win3.controls import ControlsPanel
from spotter_win3.filters import DedupCache
from spotter_win3.spot_store import SpotStore

POLL_INTERVAL_MS = 200


class ClusterWorker:
    """Owns the socket on its own daemon thread. The UI thread only ever
    reads self.incoming and calls self.send_command()/self.stop()."""

    def __init__(self, profile: ClusterProfile, callsign: str) -> None:
        self.profile = profile
        self.callsign = callsign
        self.incoming: queue.Queue = queue.Queue()
        self._outgoing: queue.Queue = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def send_command(self, command: str) -> None:
        self._outgoing.put(command)

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        host, port = self.profile.hosts[0]
        conn = ClusterConnection(host, port, self.callsign)
        try:
            conn.connect()
            self.incoming.put(("status", True))
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


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.cfg = config_module.load()
        self.store = SpotStore()
        self.dedup = DedupCache()
        self._connected = False

        root.title("DX Spotter")
        root.geometry("900x850+0+0")
        tk.Label(root, text="RBN & POTA Spotter", font=("TkDefaultFont", 16, "bold")).pack(
            pady=(8, 4)
        )
        tk.Frame(root, height=1, bg="gray").pack(fill=tk.X, padx=20, pady=4)

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
            initial_freq_mhz=self.cfg.center_freq_mhz,
            initial_bandwidth_khz=self.cfg.bandwidth_khz,
            initial_window_min=self.cfg.window_minutes,
            initial_tier=self.cfg.spotter_tier,
            cluster_name=NC7J.name,
        )
        self.controls.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        self.scope = BandScope(body)
        self.scope.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.worker: ClusterWorker | None = None
        self._start_worker()
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _start_worker(self) -> None:
        self.worker = ClusterWorker(NC7J, self.cfg.operator_callsign or "N0CALL")
        self.worker.start()
        self.worker.send_command(NC7J.filter_command(self.cfg.center_freq_mhz))

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

        self.store.prune(self.cfg.window_minutes * 60)
        self.scope.render(
            self.store.spots_for_feed("cluster"),
            self.cfg.center_freq_mhz * 1000,
            self.cfg.bandwidth_khz,
            self.cfg.window_minutes,
        )
        self.controls.set_connected(self._connected, len(self.store), NC7J.name)
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _handle_spot(self, spot: Spot) -> None:
        try:
            band = band_for_freq_mhz(spot.freq_khz / 1000)
        except ValueError:
            return
        if self.dedup.is_duplicate(spot.dx_call, band):
            return
        self.store.upsert(
            spot.dx_call, band, "cluster", spot.freq_khz, spot.spotter, spot.comment
        )

    def _on_set_band(self, freq_mhz: float) -> None:
        self.cfg.center_freq_mhz = freq_mhz
        config_module.save(self.cfg)
        assert self.worker is not None
        self.worker.send_command(NC7J.filter_command(freq_mhz))

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
