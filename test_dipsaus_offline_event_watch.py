import unittest
from dipsaus_offline_event_watch import classify_event_observation, deduplication_key


def observation(**overrides):
    row = {"symbol": "TSLA", "event_id": "earnings-2026q3",
           "event_phase": "POST_EVENT", "quote_fresh": True,
           "event_verified": True, "trend_confirmed": False,
           "downside_warning": False}
    row.update(overrides)
    return row


class EventWatchTests(unittest.TestCase):
    def test_no_entry_without_confirmation(self):
        self.assertEqual(classify_event_observation(observation())["classification"],
                         "WAIT_CONFIRMATION")

    def test_review_only_after_confirmed_post_event(self):
        result = classify_event_observation(observation(trend_confirmed=True))
        self.assertEqual(result["classification"], "REVIEW_ENTRY")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["notification_ready"])

    def test_risk_takes_precedence(self):
        result = classify_event_observation(observation(
            trend_confirmed=True, downside_warning=True))
        self.assertEqual(result["classification"], "RISK_ELEVATED")

    def test_stale_data_blocks(self):
        self.assertEqual(classify_event_observation(
            observation(quote_fresh=False))["status"], "DATA_BLOCKED")

    def test_pre_event_cannot_be_entry(self):
        self.assertEqual(classify_event_observation(
            observation(event_phase="PRE_EVENT", trend_confirmed=True))["classification"],
            "WAIT_CONFIRMATION")

    def test_duplicate_categories_share_key(self):
        a = observation(symbol="META")
        b = observation(symbol="meta", category="company_event")
        self.assertEqual(deduplication_key(a), deduplication_key(b))


if __name__ == "__main__":
    unittest.main()
