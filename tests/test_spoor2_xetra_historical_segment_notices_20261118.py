"""Offline guard for historical official exchange notices."""
import unittest
from research.spoor2_xetra_historical_segment_notices_20261118 import build_historical_segment_notice_report


class HistoricalNoticeTests(unittest.TestCase):
    def test_two_exact_isins(self):
        report = build_historical_segment_notice_report()
        self.assertEqual([r["isin_claim"] for r in report["rows"]],
                         ["DE0006231004", "DE0007030009"])

    def test_historical_notices_never_become_current_mic_proof(self):
        report = build_historical_segment_notice_report()
        for row in report["rows"]:
            self.assertEqual(row["market_label"], "Regulierter Markt - Prime Standard")
            self.assertIsNone(row["actual_segment_mic"])
            self.assertFalse(row["current_instrument_listing_attested"])
            self.assertFalse(row["current_market_segment_attested"])
            for flag in ("source_attested", "instrument_segment_verified",
                         "segment_mic_verified", "broker_route_verified",
                         "degiro_fee_verified", "trade_ready", "order_placement_enabled"):
                self.assertFalse(row[flag])

    def test_offline_no_trade_or_notification(self):
        report = build_historical_segment_notice_report()
        self.assertFalse(report["fresh_xetra_artifact_capture"])
        for flag in ("source_attested", "trade_ready", "order_placement_enabled",
                     "notify", "automatic_orders"):
            self.assertFalse(report[flag])


if __name__ == "__main__":
    unittest.main()
