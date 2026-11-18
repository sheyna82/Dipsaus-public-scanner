import unittest
from research.spoor2_xetra_current_evidence_gap_report_20261118 import (
    build_current_xetra_evidence_gap_report,
)


class CurrentXetraEvidenceGapTests(unittest.TestCase):
    def test_exact_two_pilots_and_missing_current_records(self):
        r = build_current_xetra_evidence_gap_report()
        self.assertEqual([x["isin_claim"] for x in r["rows"]],
                         ["DE0006231004", "DE0007030009"])
        for x in r["rows"]:
            self.assertFalse(x["current_record_available"])
            self.assertIn("CURRENT_INSTRUMENT_RECORD_MISSING",
                          x["current_record_comparison"]["blocks"])
            self.assertIn("TRADE_TYPE_SPECIFIC_SEGMENT_MIC", x["next_evidence_required"])
            self.assertFalse(x["trade_ready"])

    def test_no_attestation_or_download(self):
        r = build_current_xetra_evidence_gap_report()
        for key in ("source_attested", "instrument_segment_verified",
                    "segment_mic_verified", "broker_route_verified",
                    "degiro_fee_verified", "trade_ready",
                    "order_placement_enabled", "notify",
                    "automatic_orders", "external_download_performed"):
            self.assertFalse(r[key])


if __name__ == "__main__":
    unittest.main()
