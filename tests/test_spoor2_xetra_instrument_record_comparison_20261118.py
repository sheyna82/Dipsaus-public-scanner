import unittest
from research.spoor2_xetra_instrument_record_comparison_20261118 import compare_xetra_instrument_record


class XetraRecordComparisonTests(unittest.TestCase):
    def record(self):
        return {"isin": "DE0006231004", "market_mic": "XETR",
                "market_segment_status": "Active", "instrument_status": "Active",
                "market_segment": "Regulierter Markt - Prime Standard",
                "segment_mic": "XETA"}

    def test_matching_untrusted_record_never_unlocks(self):
        r = compare_xetra_instrument_record("DE0006231004", self.record())
        self.assertEqual(r["blocks"], ["BROKER_ROUTE_AND_FEES_NOT_VERIFIED",
                                        "UNTRUSTED_RECORD_NOT_INDEPENDENTLY_ATTESTED"])
        for flag in ("source_attested", "instrument_segment_verified",
                     "segment_mic_verified", "broker_route_verified",
                     "degiro_fee_verified", "trade_ready",
                     "order_placement_enabled", "notify", "automatic_orders"):
            self.assertFalse(r[flag])

    def test_isin_and_mic_conflicts_explicit(self):
        record = self.record()
        record["isin"] = "DE0007030009"
        record["market_mic"] = "XFRA"
        r = compare_xetra_instrument_record("DE0006231004", record)
        self.assertIn("ISIN_CONFLICT", r["blocks"])
        self.assertIn("OPERATING_MIC_CONFLICT", r["blocks"])

    def test_inactive_or_unknown_segment_blocks(self):
        record = self.record()
        record["market_segment_status"] = "Published"
        record["instrument_status"] = "Pending deletion"
        record["segment_mic"] = "XXXX"
        r = compare_xetra_instrument_record("DE0006231004", record)
        for block in ("MARKET_SEGMENT_NOT_REPORTED_ACTIVE",
                      "INSTRUMENT_NOT_REPORTED_ACTIVE",
                      "SEGMENT_MIC_NOT_IN_DOCUMENTED_TAXONOMY"):
            self.assertIn(block, r["blocks"])

    def test_missing_record_and_unknown_isin_fail_closed(self):
        r = compare_xetra_instrument_record("DE0007030009")
        self.assertIn("CURRENT_INSTRUMENT_RECORD_MISSING", r["blocks"])
        self.assertFalse(r["trade_ready"])
        self.assertIn("PILOT_ISIN_NOT_SUPPORTED",
                      compare_xetra_instrument_record("X", self.record())["blocks"])


if __name__ == "__main__":
    unittest.main()
