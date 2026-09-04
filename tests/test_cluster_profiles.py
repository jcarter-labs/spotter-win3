import unittest

from spotter_win3.cluster_profiles import NC7J, band_for_freq_mhz


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


if __name__ == "__main__":
    unittest.main()
