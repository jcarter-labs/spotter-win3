import unittest

from spotter_win3.scope_utils import AGE_ALPHA_FLOOR, age_alpha, in_window, y_for_freq


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


if __name__ == "__main__":
    unittest.main()
