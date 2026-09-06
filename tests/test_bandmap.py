import unittest

from spotter_win3.bandmap import MIN_LABEL_SPACING, _declutter, _label_spacing_fraction


class DeclutterTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(_declutter([]), [])

    def test_single_unchanged(self):
        self.assertEqual(_declutter([0.5]), [0.5])

    def test_well_spaced_unchanged(self):
        ys = [0.1, 0.5, 0.9]
        self.assertEqual(_declutter(ys), ys)

    def test_close_pair_pushed_apart(self):
        result = _declutter([0.5, 0.505])
        self.assertEqual(result[0], 0.5)
        self.assertGreaterEqual(result[1] - result[0], MIN_LABEL_SPACING)

    def test_cluster_pushed_apart_monotonically(self):
        result = _declutter([0.5, 0.501, 0.502, 0.503])
        for a, b in zip(result, result[1:]):
            self.assertGreaterEqual(b - a, MIN_LABEL_SPACING - 1e-9)

    def test_preserves_order(self):
        result = _declutter([0.1, 0.11, 0.12])
        self.assertEqual(result, sorted(result))

    def test_heavy_cluster_stays_within_visible_range(self):
        # Reproduces the real bug: 50 spots nearly on top of each other
        # (e.g. a busy skimmer frequency) previously got pushed off the
        # top of the plot entirely with no upper bound.
        true_ys = [0.5 + i * 0.001 for i in range(50)]
        result = _declutter(true_ys)
        self.assertLessEqual(max(result), 1.0)
        self.assertGreaterEqual(min(result), 0.0)
        self.assertEqual(result, sorted(result))

    def test_cluster_starting_near_top_does_not_overflow(self):
        true_ys = [0.9 + i * 0.001 for i in range(30)]
        result = _declutter(true_ys)
        self.assertLessEqual(max(result), 1.0)
        self.assertEqual(result, sorted(result))

    def test_custom_spacing_is_honored(self):
        result = _declutter([0.5, 0.501], spacing=0.1)
        self.assertGreaterEqual(result[1] - result[0], 0.1 - 1e-9)


class LabelSpacingFractionTests(unittest.TestCase):
    def test_taller_canvas_yields_smaller_fraction(self):
        # Reproduces the real bug: a fixed fraction meant the same 0.03
        # gave ~38px gaps (looked sparse) at a 1305px-tall window but only
        # ~25px at 850px — spacing should track pixels, not a % of
        # whatever height the window happens to be.
        short = _label_spacing_fraction(canvas_height_px=850, dpi=100)
        tall = _label_spacing_fraction(canvas_height_px=1305, dpi=100)
        self.assertGreater(short, tall)

    def test_resulting_pixel_gap_is_stable_across_heights(self):
        for height in (600, 850, 1305, 2000):
            fraction = _label_spacing_fraction(canvas_height_px=height, dpi=100)
            axes_height_px = height * (0.99 - 0.02)
            pixel_gap = fraction * axes_height_px
            expected_px = 8 * 100 / 72.0 * 1.4
            self.assertAlmostEqual(pixel_gap, expected_px, places=5)

    def test_zero_height_falls_back_to_constant(self):
        self.assertEqual(_label_spacing_fraction(canvas_height_px=0, dpi=100), MIN_LABEL_SPACING)


if __name__ == "__main__":
    unittest.main()
