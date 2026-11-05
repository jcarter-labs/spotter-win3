"""App-level wiring for the redraw gate: every state change that affects what
the scope shows must mark it dirty, and idle ticks must not repaint. Uses a
real App in a withdrawn Tk root with fake workers (no network) and a patched
config module (never touches ~/.config)."""

import queue
import time
import tkinter as tk
import unittest
from unittest import mock

from spotter_win3 import main as app_main
from spotter_win3.cluster import Spot
from spotter_win3.config import Config
from spotter_win3.pota import PotaSpot
from spotter_win3.scope_utils import FADE_REFRESH_SECONDS


class FakeWorker:
    def __init__(self, *args, **kwargs):
        self.incoming: queue.Queue = queue.Queue()
        self.commands: list[str] = []

    def start(self):
        pass

    def stop(self):
        pass

    def set_filter_commands(self, commands):
        self.commands = list(commands)


def cluster_spot(call="K1ABC", freq_khz=14045.0):
    return Spot(
        spotter="N6TV-#", dx_call=call, freq_khz=freq_khz,
        comment="CW 12 dB 22 WPM CQ", time_z="2131", raw="",
    )


def pota_spot(call="W1POTA", freq_khz=14045.0):
    return PotaSpot(
        dx_call=call, freq_khz=freq_khz, reference="US-0001",
        spotter="K1SPOT", comment="CW", spot_time="2131",
    )


class AppRedrawWiringTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"no display: {exc}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        for p in (
            mock.patch.object(app_main, "ClusterWorker", FakeWorker),
            mock.patch.object(app_main, "PotaWorker", FakeWorker),
            mock.patch.object(app_main.config_module, "load", return_value=Config()),
            mock.patch.object(app_main.config_module, "save"),
        ):
            p.start()
            self.addCleanup(p.stop)
        # No self-rescheduling timer: tests drive _poll() by hand.
        self.root.after = mock.Mock()
        self.app = app_main.App(self.root)
        self.render = mock.Mock()
        self.app.scope.render = self.render
        self.app._poll()  # first poll always paints and clears the dirty flag
        self.render.reset_mock()

    def assertRendersOnceThenIdle(self):
        self.app._poll()
        self.assertEqual(self.render.call_count, 1)
        self.app._poll()
        self.assertEqual(self.render.call_count, 1, "second tick should be idle")

    def test_idle_tick_does_not_render(self):
        self.app._poll()
        self.app._poll()
        self.render.assert_not_called()

    def test_fade_refresh_renders_after_interval(self):
        later = time.monotonic() + FADE_REFRESH_SECONDS + 0.1
        with mock.patch.object(app_main.time, "monotonic", return_value=later):
            self.app._poll()
        self.assertEqual(self.render.call_count, 1)

    def test_new_cluster_spot_renders(self):
        self.app.worker.incoming.put(("spot", cluster_spot()))
        self.assertRendersOnceThenIdle()

    def test_duplicate_cluster_spot_does_not_render(self):
        self.app.worker.incoming.put(("spot", cluster_spot()))
        self.app._poll()
        self.render.reset_mock()
        self.app.worker.incoming.put(("spot", cluster_spot()))  # dedup window
        self.app._poll()
        self.render.assert_not_called()

    def test_new_pota_spot_renders(self):
        self.app.pota_worker.incoming.put(("spot", pota_spot()))
        self.assertRendersOnceThenIdle()

    def test_prune_removing_a_spot_renders(self):
        self.app.store.upsert(
            "OLD1", "20m", "cluster", 14045.0, "S", "CW",
            now=time.monotonic() - 10 * self.app.cfg.window_minutes * 60,
        )
        self.assertRendersOnceThenIdle()
        self.assertEqual(len(self.app.store), 0)

    def test_canvas_resize_renders(self):
        # Tk drops <Configure> for unmapped windows, so show it and resize for real.
        self.root.deiconify()
        self.root.update()
        self.app._poll()
        self.render.reset_mock()
        self.root.geometry("500x900+0+0")
        self.root.update()
        self.assertRendersOnceThenIdle()

    def test_valid_band_change_renders(self):
        self.assertIsNone(self.app._on_set_band(14.045))
        self.assertRendersOnceThenIdle()

    def test_rejected_band_change_does_not_render(self):
        self.assertIsInstance(self.app._on_set_band(1.0), str)
        self.app._poll()
        self.render.assert_not_called()

    def test_bandwidth_change_renders(self):
        self.app._on_bandwidth_change(100)
        self.assertRendersOnceThenIdle()

    def test_window_change_renders(self):
        self.app._on_window_change(5)
        self.assertRendersOnceThenIdle()

    def test_clear_renders_and_empties_store(self):
        self.app.store.upsert("K1ABC", "20m", "cluster", 14045.0, "S", "CW")
        self.app._on_clear()
        self.assertRendersOnceThenIdle()
        self.assertEqual(len(self.app.store), 0)

    def test_server_change_renders(self):
        self.app._on_server_change("W3LPL (DXSpider)")
        self.assertRendersOnceThenIdle()

    def test_server_change_to_same_profile_does_not_render(self):
        self.app._on_server_change(self.app.profile.name)
        self.app._poll()
        self.render.assert_not_called()


if __name__ == "__main__":
    unittest.main()
