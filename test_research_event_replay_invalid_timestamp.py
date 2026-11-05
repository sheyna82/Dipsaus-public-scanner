import unittest
from datetime import datetime, timezone
from research_event_replay_intake_202610 import CASES, eligible_replay

class ReplayInvalidTimestampTests(unittest.TestCase):
    def test_string_alert_timestamp_fails_closed(self):
        self.assertFalse(eligible_replay(
            CASES[0], alert_timestamp="2026-10-22T11:33:00Z",
            timestamped_bars=[{"timestamp": datetime(2026, 10, 23, tzinfo=timezone.utc),
                               "open": 10, "high": 11, "low": 9, "close": 10, "volume": 100}],
            signal_snapshot={"ticker": "TSLA", "source_id": "test", "origin": "independent_archive",
                             "created_at": datetime(2026, 10, 22, tzinfo=timezone.utc)},
            alert_evidence={"verified": True, "source_id": "test", "origin": "independent_archive"},
            price_evidence={"verified": True, "source_id": "test", "origin": "independent_archive"}))

if __name__ == "__main__":
    unittest.main()
