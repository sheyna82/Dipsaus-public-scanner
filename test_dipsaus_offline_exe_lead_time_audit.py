import unittest
from datetime import datetime, timedelta, timezone
from dipsaus_offline_exe_lead_time_audit import audit_downside_lead_time


def fixture():
    start = datetime(2026, 10, 22, 13, 30, tzinfo=timezone.utc)
    bars = [{"open": 100., "high": 100.2, "low": 99.5, "close": 100.}
            for _ in range(30)]
    for i in range(5):
        bars.append({"open": 98.8-i*.2, "high": 99.-i*.2,
                     "low": 98.4-i*.2, "close": 98.5-i*.2})
    return [(start+timedelta(minutes=i), bar) for i, bar in enumerate(bars)]


class LeadTimeAuditTests(unittest.TestCase):
    def test_no_early_claim_when_threshold_not_crossed(self):
        result = audit_downside_lead_time(fixture())
        self.assertEqual(result["status"], "DESCRIPTIVE_LEAD_TIME")
        self.assertEqual(result["first_signal_available_utc"], "2026-10-22T14:03:00+00:00")
        self.assertIsNone(result["lead_minutes"])
        self.assertIsNone(result["alert_before_decline"])

    def test_crossing_same_candle_not_early(self):
        bars = fixture()
        result = audit_downside_lead_time(bars, decline_pct=1.5)
        self.assertEqual(result["status"], "DESCRIPTIVE_LEAD_TIME")
        self.assertFalse(result["alert_before_decline"])

    def test_gap_blocks(self):
        bars = fixture()
        bars[5] = (bars[5][0]+timedelta(minutes=1), bars[5][1])
        self.assertEqual(audit_downside_lead_time(bars)["status"], "DATA_BLOCKED")

    def test_invalid_threshold_blocks(self):
        self.assertEqual(audit_downside_lead_time(fixture(), decline_pct=0)["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
