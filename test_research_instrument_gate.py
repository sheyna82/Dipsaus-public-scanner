"""Offline instrument identity and fail-closed route tests."""
import unittest
from research_instrument_gate import assess_instrument, isin_checksum_valid


class InstrumentTests(unittest.TestCase):
    def setUp(self):
        self.e = {"isin": "NL0010273215", "operating_mic": "XAMS",
                  "isin_source_verified": True, "mic_source_verified": True,
                  "instrument_active_verified": True, "segment_verified": True,
                  "broker_route_verified": True, "broker_fee_verified": True}

    def test_known_isin_checksum(self):
        self.assertTrue(isin_checksum_valid("NL0010273215"))

    def test_bad_check_digit(self):
        self.assertFalse(isin_checksum_valid("NL0010273216"))

    def test_malformed_isin(self):
        self.assertFalse(isin_checksum_valid("ACCOUNT1234"))

    def test_complete_claims_still_non_executable(self):
        r = assess_instrument(self.e)
        self.assertEqual(r["status"], "INSTRUMENT_RESEARCH_REVIEW")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["source_authenticity_independently_verified"])

    def test_missing_broker_route(self):
        del self.e["broker_route_verified"]
        self.assertEqual(assess_instrument(self.e)["reason"], "MISSING_VERIFICATION")

    def test_unverified_broker_route(self):
        self.e["broker_route_verified"] = False
        self.assertEqual(assess_instrument(self.e)["reason"], "UNVERIFIED")

    def test_unverified_market_segment(self):
        self.e["segment_verified"] = False
        self.assertEqual(assess_instrument(self.e)["reason"], "UNVERIFIED")

    def test_bad_mic(self):
        self.e["operating_mic"] = "XETRA"
        self.assertEqual(assess_instrument(self.e)["reason"], "INVALID_MIC")

    def test_missing_fee_verification(self):
        self.e["broker_fee_verified"] = None
        self.assertEqual(assess_instrument(self.e)["reason"], "MISSING_VERIFICATION")

    def test_bad_isin_blocks_even_verified_flags(self):
        self.e["isin"] = "NL0010273216"
        self.assertEqual(assess_instrument(self.e)["reason"], "INVALID_ISIN")


if __name__ == "__main__":
    unittest.main()
