import unittest

from spotter_win3.bandmap import MIN_LABEL_SPACING, _declutter


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


if __name__ == "__main__":
    unittest.main()
