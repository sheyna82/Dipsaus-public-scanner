import unittest
from research_event_private_notification_inventory import notification_evidence_inventory

class NotificationDeduplicationTests(unittest.TestCase):
    def test_identical_alert_records_count_once(self):
        state = {"signals": {
            "event|TSLA|a": {"notified_utc": "2026-10-22T11:33:00Z"},
            "event|TSLA|b": {"notified_utc": "2026-10-22T11:33:00Z"},
            "event|TSLA|c": {"notified_utc": "2026-10-22T12:33:00Z"},
        }}
        report = notification_evidence_inventory(state)
        self.assertEqual(len(report["cases"]["TSLA"]), 2)
        self.assertFalse(report["delivery_proof_available"])
        self.assertFalse(report["historical_profit_claim_allowed"])

if __name__ == "__main__":
    unittest.main()
