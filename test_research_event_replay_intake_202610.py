import unittest
from datetime import datetime, timezone
from research_event_replay_intake_202610 import CASES, validate_cases, eligible_replay

class EventReplayIntakeTests(unittest.TestCase):
    def test_case_classification(self):
        self.assertTrue(validate_cases())
        self.assertEqual({c["ticker"] for c in CASES}, {"TSLA", "META", "COHU", "AMZN"})

    def test_no_timestamp_no_trade(self):
        self.assertTrue(all(not eligible_replay(c) for c in CASES))

    def test_future_snapshot_rejected(self):
        alert = datetime(2026, 10, 22, 7, 33, tzinfo=timezone.utc)
        bars = [{"timestamp": datetime(2026, 10, 23, tzinfo=timezone.utc)}]
        future = {"created_at": datetime(2026, 10, 24, tzinfo=timezone.utc)}
        self.assertFalse(eligible_replay(CASES[0], alert_timestamp=alert,
                                         timestamped_bars=bars, signal_snapshot=future))

    def test_prior_snapshot_and_later_bar(self):
        alert = datetime(2026, 10, 22, 7, 33, tzinfo=timezone.utc)
        bars = [{"timestamp": datetime(2026, 10, 23, tzinfo=timezone.utc)}]
        prior = {"created_at": datetime(2026, 10, 22, 7, 30, tzinfo=timezone.utc)}
        self.assertTrue(eligible_replay(CASES[0], alert_timestamp=alert,
                                        timestamped_bars=bars, signal_snapshot=prior))

if __name__ == "__main__":
    unittest.main()
