import unittest

from spotter_win3.scope_utils import (
    AGE_ALPHA_FLOOR,
    FADE_REFRESH_SECONDS,
    RedrawGate,
    age_alpha,
    in_window,
    y_for_freq,
)


class YForFreqTests(unittest.TestCase):
    def test_center_is_midpoint(self):
        self.assertAlmostEqual(y_for_freq(14045.0, 14045.0, 50), 0.5)

    def test_bottom_and_top_edges(self):
        self.assertAlmostEqual(y_for_freq(14020.0, 14045.0, 50), 0.0)
        self.assertAlmostEqual(y_for_freq(14070.0, 14045.0, 50), 1.0)


class InWindowTests(unittest.TestCase):
    def test_inside(self):
        self.assertTrue(in_window(14045.0, 14045.0, 50))

    def test_outside(self):
        self.assertFalse(in_window(14000.0, 14045.0, 50))

    def test_edge_inclusive(self):
        self.assertTrue(in_window(14020.0, 14045.0, 50))


class AgeAlphaTests(unittest.TestCase):
    def test_fresh_spot_is_full_alpha(self):
        self.assertAlmostEqual(age_alpha(0.0, 600.0), 1.0)

    def test_alpha_never_below_floor(self):
        self.assertAlmostEqual(age_alpha(10_000.0, 600.0), AGE_ALPHA_FLOOR)

    def test_alpha_at_floor_never_zero(self):
        self.assertGreater(age_alpha(10_000.0, 600.0), 0.0)

    def test_halfway_aged(self):
        alpha = age_alpha(300.0, 600.0)
        self.assertGreater(alpha, AGE_ALPHA_FLOOR)
        self.assertLess(alpha, 1.0)


class RedrawGateTests(unittest.TestCase):
    def test_first_call_always_redraws(self):
        self.assertTrue(RedrawGate().should_redraw(100.0))

    def test_idle_ticks_are_skipped_until_fade_refresh(self):
        gate = RedrawGate(fade_refresh_seconds=2.0)
        gate.should_redraw(100.0)
        for t in (100.2, 100.4, 100.6, 100.8, 101.0, 101.2, 101.4, 101.6, 101.8):
            self.assertFalse(gate.should_redraw(t), t)
        self.assertTrue(gate.should_redraw(102.0))

    def test_dirty_forces_redraw_then_clears(self):
        gate = RedrawGate(fade_refresh_seconds=2.0)
        gate.should_redraw(100.0)
        gate.mark_dirty()
        self.assertTrue(gate.should_redraw(100.2))
        self.assertFalse(gate.should_redraw(100.4))

    def test_redraw_resets_the_fade_clock(self):
        gate = RedrawGate(fade_refresh_seconds=2.0)
        gate.should_redraw(100.0)
        gate.mark_dirty()
        gate.should_redraw(101.5)  # event redraw at 101.5
        self.assertFalse(gate.should_redraw(103.4))  # only 1.9 s since
        self.assertTrue(gate.should_redraw(103.5))

    def test_many_marks_between_ticks_coalesce_to_one_redraw(self):
        gate = RedrawGate()
        gate.should_redraw(100.0)
        for _ in range(50):
            gate.mark_dirty()
        self.assertTrue(gate.should_redraw(100.2))
        self.assertFalse(gate.should_redraw(100.4))

    def test_default_fade_refresh_is_invisible_at_shortest_window(self):
        # Alpha moves at most (1 - floor) / 60 per second on a 1-minute window;
        # one refresh interval must stay under ~3 % alpha so aging looks smooth.
        step = (1.0 - AGE_ALPHA_FLOOR) / 60 * FADE_REFRESH_SECONDS
        self.assertLess(step, 0.03)


if __name__ == "__main__":
    unittest.main()
