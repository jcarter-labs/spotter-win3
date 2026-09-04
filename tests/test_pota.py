import unittest

from spotter_win3.pota import parse_pota_record

# Captured live from https://api.pota.app/spot/activator via
# scripts/diag_pota_api.py on 2026-09-04 — not fabricated examples.
REAL_CW_RECORD = {
    "spotId": 56129204,
    "activator": "W1AW/4",
    "frequency": "14036.0",
    "mode": "CW",
    "reference": "US-3844",
    "parkName": None,
    "spotTime": "2026-09-04T21:59:44",
    "spotter": "SP5GQ-#",
    "comments": "RBN 10 dB 22 WPM via SP5GQ-#",
    "source": "RBN",
    "invalid": None,
    "name": "Jordan Lake State Recreation Area",
    "locationDesc": "US-NC",
    "grid4": "FM05",
    "grid6": "FM05lr",
    "latitude": 35.7369,
    "longitude": -79.0169,
    "count": 67,
    "expire": 466,
}


class ParsePotaRecordTests(unittest.TestCase):
    def test_real_cw_record_fields(self):
        spot = parse_pota_record(REAL_CW_RECORD)
        self.assertIsNotNone(spot)
        self.assertEqual(spot.dx_call, "W1AW/4")
        self.assertEqual(spot.freq_khz, 14036.0)
        self.assertEqual(spot.reference, "US-3844")
        self.assertEqual(spot.spotter, "SP5GQ-#")
        self.assertIn("WPM", spot.comment)

    def test_non_cw_mode_is_filtered_out(self):
        record = dict(REAL_CW_RECORD, mode="SSB")
        self.assertIsNone(parse_pota_record(record))

    def test_missing_required_field_returns_none(self):
        record = dict(REAL_CW_RECORD)
        del record["activator"]
        self.assertIsNone(parse_pota_record(record))

    def test_missing_spotter_defaults_empty(self):
        record = dict(REAL_CW_RECORD)
        del record["spotter"]
        spot = parse_pota_record(record)
        self.assertEqual(spot.spotter, "")

    def test_null_comments_defaults_empty(self):
        record = dict(REAL_CW_RECORD, comments=None)
        spot = parse_pota_record(record)
        self.assertEqual(spot.comment, "")


if __name__ == "__main__":
    unittest.main()
