"""Synthetic-only ISIN/MIC gate tests. No real market admission claims."""
import unittest
from research.spoor2_instrument_reference_gate_20261114 import inspect_instrument_reference

ISIN = "US0378331005"
MIC = "XNAS"


class InstrumentReferenceTests(unittest.TestCase):
    def test_valid_identifier_without_evidence_blocks(self):
        r = inspect_instrument_reference(ISIN, MIC)
        self.assertTrue(r["identifier_syntax_valid"])
        self.assertEqual(r["blocks"], ["INDEPENDENT_REFERENCE_REQUIRED"])
        self.assertFalse(r["trade_ready"])

    def test_exact_pair_still_does_not_attest(self):
        r = inspect_instrument_reference(ISIN, MIC, ((ISIN, MIC),))
        self.assertTrue(r["reviewed_pair_match"])
        for flag in ("source_attested", "instrument_segment_verified",
                     "broker_route_verified", "trade_ready", "order_placement_enabled"):
            self.assertFalse(r[flag])

    def test_different_mic_blocks(self):
        r = inspect_instrument_reference(ISIN, "XETR", ((ISIN, MIC),))
        self.assertEqual(r["blocks"], ["UNVERIFIED_INSTRUMENT_MARKET_PAIR"])

    def test_bad_isin_checksum_blocks(self):
        r = inspect_instrument_reference("US0378331006", MIC, ((ISIN, MIC),))
        self.assertEqual(r["blocks"], ["INVALID_ISIN"])

    def test_lowercase_mic_blocks(self):
        self.assertEqual(inspect_instrument_reference(ISIN, "xnas")["blocks"], ["INVALID_MIC"])

    def test_unknown_mic_format_blocks(self):
        self.assertEqual(inspect_instrument_reference(ISIN, "ABCDE")["blocks"], ["INVALID_MIC"])

    def test_non_string_isin_blocks(self):
        self.assertEqual(inspect_instrument_reference(None, MIC)["blocks"], ["INVALID_ISIN"])

    def test_bad_reference_shape_blocks(self):
        r = inspect_instrument_reference(ISIN, MIC, [(ISIN, MIC)])
        self.assertEqual(r["blocks"], ["INDEPENDENT_REFERENCE_REQUIRED"])


if __name__ == "__main__":
    unittest.main()
