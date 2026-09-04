import tempfile
import unittest
from pathlib import Path

from spotter_win3.config import Config, load, save


class ConfigRoundTripTests(unittest.TestCase):
    def test_load_missing_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            config = load(path)
            self.assertEqual(config, Config())

    def test_save_then_load_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "config.json"
            original = Config(
                operator_callsign="N6YU",
                center_freq_mhz=14.045,
                bandwidth_khz=50,
                window_minutes=10,
                spotter_tier="local",
                spotter_lists={"local": ["W6YX", "N6TV-#"], "regional": []},
            )
            save(original, path)
            self.assertTrue(path.exists())
            loaded = load(path)
            self.assertEqual(loaded, original)

    def test_load_partial_file_fills_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text('{"operator_callsign": "N6YU"}', encoding="utf-8")
            loaded = load(path)
            self.assertEqual(loaded.operator_callsign, "N6YU")
            self.assertEqual(loaded.center_freq_mhz, Config().center_freq_mhz)


if __name__ == "__main__":
    unittest.main()
