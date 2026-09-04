import unittest

from spotter_win3.cluster import parse_spot_line

# Captured live from dxc.nc7j.com:7373 via scripts/diag_cluster_capture.py
# on 2026-09-04 21:31-21:32Z — not fabricated examples.
CAPTURED_LINES = [
    "DX de N6TV-#:    14040.0  N7BBQ        CW 12 dB 22 WPM CQ             2131Z",
    "DX de W6YX-#:    18079.0  AG5XU        CW 17 dB 14 WPM CQ             2131Z",
    "DX de W6YX-#:    14060.9  W1WC         CW 14 dB 22 WPM CQ             2131Z",
    "DX de W6YX-#:    14040.0  N7BBQ        CW 17 dB 22 WPM CQ             2131Z",
    "DX de N6TV-#:    14045.0  W1ND         CW 4 dB 27 WPM CQ              2132Z",
    "DX de W6YX-#:    14045.1  W1ND         CW 14 dB 28 WPM CQ             2132Z",
]


class ParseSpotLineTests(unittest.TestCase):
    def test_skimmer_spot_fields(self):
        spot = parse_spot_line(CAPTURED_LINES[0])
        self.assertIsNotNone(spot)
        self.assertEqual(spot.spotter, "N6TV-#")
        self.assertEqual(spot.dx_call, "N7BBQ")
        self.assertEqual(spot.freq_khz, 14040.0)
        self.assertEqual(spot.time_z, "2131")
        self.assertIn("CW", spot.comment)

    def test_all_captured_lines_parse(self):
        for line in CAPTURED_LINES:
            with self.subTest(line=line):
                self.assertIsNotNone(parse_spot_line(line))

    def test_non_spot_prompt_line_returns_none(self):
        self.assertIsNone(parse_spot_line("N6YU de NC7J 04-Sep 2131Z arc6>"))

    def test_blank_line_returns_none(self):
        self.assertIsNone(parse_spot_line(""))


if __name__ == "__main__":
    unittest.main()
