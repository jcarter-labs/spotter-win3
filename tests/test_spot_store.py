import unittest

from spotter_win3.spot_store import SpotStore


class SpotStoreTests(unittest.TestCase):
    def test_upsert_and_len(self):
        store = SpotStore()
        store.upsert("N7BBQ", "20", "cluster", 14040.0, "N6TV-#", "CW 12 dB", now=0.0)
        self.assertEqual(len(store), 1)

    def test_same_key_updates_not_duplicates(self):
        store = SpotStore()
        store.upsert("N7BBQ", "20", "cluster", 14040.0, "N6TV-#", "CW 12 dB", now=0.0)
        store.upsert("N7BBQ", "20", "cluster", 14040.1, "N6TV-#", "CW 14 dB", now=5.0)
        self.assertEqual(len(store), 1)
        spot = store.spots_for_feed("cluster")[0]
        self.assertEqual(spot.freq_khz, 14040.1)
        self.assertEqual(spot.last_seen, 5.0)

    def test_cluster_and_pota_do_not_evict_each_other(self):
        store = SpotStore()
        store.upsert("N7BBQ", "20", "cluster", 14040.0, "N6TV-#", "CW", now=0.0)
        store.upsert("N7BBQ", "20", "pota", 14040.0, "", "", now=0.0)
        self.assertEqual(len(store), 2)

    def test_prune_removes_stale_entries_only(self):
        store = SpotStore()
        store.upsert("OLD", "20", "cluster", 14040.0, "X", "", now=0.0)
        store.upsert("NEW", "20", "cluster", 14040.0, "X", "", now=100.0)
        store.prune(horizon_seconds=60, now=100.0)
        calls = {s.dx_call for s in store.spots_for_feed("cluster")}
        self.assertEqual(calls, {"NEW"})

    def test_spots_for_feed_filters_by_feed(self):
        store = SpotStore()
        store.upsert("A", "20", "cluster", 14040.0, "X", "", now=0.0)
        store.upsert("B", "20", "pota", 14040.0, "", "", now=0.0)
        self.assertEqual([s.dx_call for s in store.spots_for_feed("cluster")], ["A"])
        self.assertEqual([s.dx_call for s in store.spots_for_feed("pota")], ["B"])


if __name__ == "__main__":
    unittest.main()
