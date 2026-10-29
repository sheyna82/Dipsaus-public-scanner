"""Private matching regression tests with synthetic, non-sensitive records."""
import unittest
from research_scanner_private_notification_match import match_observed_notifications


class PrivateNotificationMatchTests(unittest.TestCase):
    def state(self, records):
        return {"signals": records}

    def test_empty_state_has_eight_missing_cases(self):
        result = match_observed_notifications(self.state({}))
        self.assertEqual(result["observation_count"], 8)
        self.assertTrue(all(r["match_status"] == "no_matching_utc_day_record"
                            for r in result["cases"]))

    def test_unique_candidate_is_not_verified_link(self):
        state = self.state({"EARLY_RECOVERY|VIST": {
            "notified_utc": "2026-10-26T12:51:00Z", "delivery": "sent"}})
        result = match_observed_notifications(state)
        row = next(r for r in result["cases"] if r["symbol"] == "VIST")
        self.assertEqual(row["candidate_private_record_count"], 1)
        self.assertFalse(row["screenshot_link_verified"])
        self.assertFalse(row["phone_delivery_verified"])

    def test_ambiguous_records_are_not_silently_resolved(self):
        state = self.state({
            "PREALERT|VIST": {"notified_utc": "2026-10-26T12:51:00Z"},
            "RECOVERY|VIST": {"notified_utc": "2026-10-26T12:52:00Z"},
        })
        result = match_observed_notifications(state)
        row = next(r for r in result["cases"] if r["symbol"] == "VIST")
        self.assertEqual(row["match_status"], "ambiguous_multiple_utc_day_records")

    def test_private_timestamps_not_exported(self):
        state = self.state({"EARLY_RECOVERY|VIST": {
            "notified_utc": "2026-10-26T12:51:00Z"}})
        result = match_observed_notifications(state)
        self.assertNotIn("2026-10-26T12:51:00", str(result))


if __name__ == "__main__":
    unittest.main()
