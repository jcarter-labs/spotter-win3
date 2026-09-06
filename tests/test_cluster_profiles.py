import unittest

from spotter_win3.cluster_profiles import (
    NC7J,
    PROFILES,
    W3LPL,
    W4MYA,
    WA9PIE2,
    band_for_freq_mhz,
)


class BandForFreqTests(unittest.TestCase):
    def test_known_bands(self):
        self.assertEqual(band_for_freq_mhz(14.045), "20")
        self.assertEqual(band_for_freq_mhz(7.030), "40")
        self.assertEqual(band_for_freq_mhz(21.050), "15")
        self.assertEqual(band_for_freq_mhz(18.100), "17")

    def test_out_of_band_raises(self):
        with self.assertRaises(ValueError):
            band_for_freq_mhz(6.0)


class NC7JProfileTests(unittest.TestCase):
    def test_filter_command_format(self):
        # Format confirmed live: server accepted "set dx filter mode=cw"
        # (scripts/diag_cluster_filter_fields.py) and echoed it back as
        # "mode = cw" in show/dx/filter.
        self.assertEqual(
            NC7J.filter_command(14.045), "set dx filter mode = cw and band = 20"
        )

    def test_cw_trustworthy(self):
        self.assertTrue(NC7J.cw_trustworthy)

    def test_hosts(self):
        self.assertEqual(NC7J.hosts, (("dxc.nc7j.com", 7373),))


class WA9PIE2ProfileTests(unittest.TestCase):
    def test_filter_commands(self):
        # Confirmed live: scripts/diag_wa9pie_verify_filter.py and
        # diag_wa9pie_verify_rbn_filter.py — both accepted and echoed
        # back unchanged in show/filter.
        self.assertEqual(
            WA9PIE2.filter_commands(14.045),
            ["accept/spots on 20m/cw", "accept/rbn on 20m/cw"],
        )

    def test_cw_trustworthy(self):
        self.assertTrue(WA9PIE2.cw_trustworthy)

    def test_hosts(self):
        self.assertEqual(WA9PIE2.hosts, (("dxc.wa9pie.net", 8000),))


class W3LPLProfileTests(unittest.TestCase):
    def test_filter_commands_same_dxspider_dialect(self):
        # Confirmed live: scripts/diag_w3lpl_verify.py — same DXSpider
        # dialect as WA9PIE-2, re-confirmed rather than rediscovered.
        self.assertEqual(
            W3LPL.filter_commands(21.050),
            ["accept/spots on 15m/cw", "accept/rbn on 15m/cw"],
        )

    def test_hosts(self):
        self.assertEqual(W3LPL.hosts, (("w3lpl.net", 7373),))


class W4MYAProfileTests(unittest.TestCase):
    def test_filter_command_rejects_all_non_cw_slots(self):
        # Confirmed live: scripts/diag_w4mya_dxbm_filter.py — the server
        # accepted this exact command and echoed it back in SH/FILTER
        # DXBM, and subsequent spots were exclusively CW. Real syntax
        # comes from the CC User Manual (Appendix B/C), not a guess.
        command = W4MYA.filter_command(14.045)
        self.assertTrue(command.startswith("SET/FILTER DXBM/REJECT "))
        self.assertIn("20-RTTY", command)
        self.assertIn("20-SSB", command)
        self.assertNotIn("20-CW", command)

    def test_filter_command_same_regardless_of_band(self):
        # DXBM rejects segments across all bands at once, not per-band.
        self.assertEqual(W4MYA.filter_commands(14.045), W4MYA.filter_commands(21.05))

    def test_out_of_band_still_raises(self):
        # Must still validate consistently with other profiles.
        with self.assertRaises(ValueError):
            W4MYA.filter_commands(6.0)

    def test_cw_trustworthy(self):
        # Server-side mode filtering verified live — no client-side
        # fallback needed for this profile.
        self.assertTrue(W4MYA.cw_trustworthy)

    def test_hosts(self):
        self.assertEqual(W4MYA.hosts, (("dxc.w4mya.us", 7373),))


class ProfileRegistryTests(unittest.TestCase):
    def test_all_four_profiles_registered(self):
        self.assertEqual(
            set(PROFILES.keys()),
            {NC7J.name, WA9PIE2.name, W3LPL.name, W4MYA.name},
        )

    def test_lookup_by_name(self):
        self.assertIs(PROFILES[NC7J.name], NC7J)


if __name__ == "__main__":
    unittest.main()
