import unittest
from unittest.mock import patch
from research.spoor2_xetra_evidence_reconciliation_20261118 import (
    build_xetra_reconciled_evidence_report,
)


class XetraReconciliationTests(unittest.TestCase):
    def test_uploaded_records_are_present_but_unattested(self):
        report = build_xetra_reconciled_evidence_report()
        self.assertEqual(report["status"], "BLOCKED_WITH_UPLOADED_RECORDS")
        self.assertEqual([r["isin"] for r in report["rows"]],
                         ["DE0006231004", "DE0007030009"])
        for row in report["rows"]:
            self.assertFalse(row["historical_report_record_available"])
            self.assertTrue(row["uploaded_record_available"])
            self.assertIsNone(row["segment_mic"])
            self.assertFalse(row["trade_ready"])
            self.assertIn("INDEPENDENT_SOURCE_ORIGIN_AND_ARTIFACT_INTEGRITY",
                          row["remaining_evidence_required"])

    def test_all_authorization_flags_remain_false(self):
        report = build_xetra_reconciled_evidence_report()
        for key in ("source_attested", "instrument_segment_verified",
                    "segment_mic_verified", "broker_route_verified",
                    "degiro_fee_verified", "trade_ready", "order_placement_enabled",
                    "notify", "automatic_orders", "external_download_performed"):
            self.assertFalse(report[key])

    def test_unexpected_historical_suffix_fails_closed(self):
        from research.spoor2_xetra_historical_segment_notices_20261118 import NOTICES
        from copy import deepcopy
        fake = deepcopy(NOTICES)
        fake["DE0006231004"]["symbol_claim"] = "IFX.US"
        with patch("research.spoor2_xetra_current_evidence_gap_report_20261118.NOTICES", fake):
            with self.assertRaisesRegex(ValueError, "SYMBOL_MISMATCH"):
                build_xetra_reconciled_evidence_report()

    def test_mismatched_instruments_fail_closed(self):
        fake = {"rows": [{"isin": "INVALID"}], **{
            key: False for key in ("source_attested", "instrument_segment_verified",
                                   "segment_mic_verified", "broker_route_verified",
                                   "degiro_fee_verified", "trade_ready",
                                   "order_placement_enabled", "notify",
                                   "automatic_orders")}}
        with patch("research.spoor2_xetra_evidence_reconciliation_20261118.build_uploaded_xetra_evidence_report", return_value=fake):
            with self.assertRaisesRegex(ValueError, "INSTRUMENT_SET_MISMATCH"):
                build_xetra_reconciled_evidence_report()


if __name__ == "__main__":
    unittest.main()
