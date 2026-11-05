import unittest

from scripts.profile_hotpaths import make_spot_lines, populate_store
from spotter_win3.cluster import parse_spot_line
from spotter_win3.spot_store import SpotStore


class SyntheticSpotTests(unittest.TestCase):
    def test_every_generated_line_parses_as_cw_in_band(self):
        for line in make_spot_lines(500):
            spot = parse_spot_line(line)
            self.assertIsNotNone(spot, line)
            self.assertIn("CW", spot.comment)
            self.assertTrue(14000.0 <= spot.freq_khz <= 14350.0)

    def test_generation_is_deterministic_per_seed(self):
        self.assertEqual(make_spot_lines(50, seed=3), make_spot_lines(50, seed=3))
        self.assertNotEqual(make_spot_lines(50, seed=3), make_spot_lines(50, seed=4))

    def test_populate_store_splits_feeds(self):
        store = SpotStore()
        populate_store(store, 12, 5, now=1000.0)
        self.assertEqual(len(store.spots_for_feed("cluster")), 12)
        self.assertEqual(len(store.spots_for_feed("pota")), 5)


if __name__ == "__main__":
    unittest.main()
