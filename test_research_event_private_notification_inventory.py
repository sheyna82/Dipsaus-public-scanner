import unittest
from research_event_private_notification_inventory import notification_evidence_inventory

class PrivateNotificationInventoryTests(unittest.TestCase):
    def test_empty_state_does_not_invent_alerts(self):
        report = notification_evidence_inventory({"signals": {}})
        self.assertEqual(report["missing_notification_timestamps"],
                         ["AMZN", "COHU", "META", "TSLA"])
        self.assertFalse(report["historical_profit_claim_allowed"])

    def test_private_timestamp_is_not_delivery_proof(self):
        state = {"signals": {
            "event|TSLA|earnings": {"notified_utc": "2026-10-22T11:33:00Z",
                                   "delivery": "unknown"},
            "event|OTHER|earnings": {"notified_utc": "2026-10-22T11:33:00Z"}
        }}
        report = notification_evidence_inventory(state)
        self.assertEqual(len(report["cases"]["TSLA"]), 1)
        self.assertFalse(report["cases"]["TSLA"][0]["push_delivery_independently_verified"])
        self.assertFalse(report["private_state_exported"])

if __name__ == "__main__":
    unittest.main()
