import unittest

from spotter_win3.cluster import Spot
from spotter_win3.filters import DedupCache, is_cw_mode, matches_spotter_tier


def _spot(comment: str) -> Spot:
    return Spot(
        spotter="N6TV-#",
        dx_call="N7BBQ",
        freq_khz=14040.0,
        comment=comment,
        time_z="2131",
        raw="",
    )


class DedupCacheTests(unittest.TestCase):
    def test_first_sighting_not_duplicate(self):
        cache = DedupCache()
        self.assertFalse(cache.is_duplicate("N7BBQ", "20", now=0.0))

    def test_repeat_within_window_is_duplicate(self):
        cache = DedupCache()
        cache.is_duplicate("N7BBQ", "20", now=0.0)
        self.assertTrue(cache.is_duplicate("N7BBQ", "20", now=60.0))

    def test_repeat_after_window_not_duplicate(self):
        cache = DedupCache()
        cache.is_duplicate("N7BBQ", "20", now=0.0)
        self.assertFalse(cache.is_duplicate("N7BBQ", "20", now=121.0))

    def test_different_band_not_duplicate(self):
        cache = DedupCache()
        cache.is_duplicate("N7BBQ", "20", now=0.0)
        self.assertFalse(cache.is_duplicate("N7BBQ", "15", now=1.0))


class SpotterTierTests(unittest.TestCase):
    def test_case_insensitive_match(self):
        self.assertTrue(matches_spotter_tier("n6tv-#", {"N6TV-#"}))

    def test_no_match(self):
        self.assertFalse(matches_spotter_tier("K1ABC", {"N6TV-#"}))


class CwModeCheckTests(unittest.TestCase):
    def test_real_skimmer_comment_is_cw(self):
        self.assertTrue(is_cw_mode(_spot("CW 12 dB 22 WPM CQ")))

    def test_non_cw_comment(self):
        self.assertFalse(is_cw_mode(_spot("RTTY 5NN TU")))

    def test_empty_comment(self):
        self.assertFalse(is_cw_mode(_spot("")))


if __name__ == "__main__":
    unittest.main()
