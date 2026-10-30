import unittest
from datetime import datetime, timezone
from research_event_replay_intake_202610 import CASES, eligible_replay

class CompleteEventEvidenceTests(unittest.TestCase):
    def test_synthetic_fixture_is_not_independently_verified(self):
        alert = datetime(2026, 10, 22, 11, 33, tzinfo=timezone.utc)
        bars = [{"timestamp": datetime(2026, 10, 23, 20, tzinfo=timezone.utc),
                 "open": 100, "high": 105, "low": 99, "close": 103, "volume": 10000}]
        snapshot = {"created_at": datetime(2026, 10, 22, 11, 30, tzinfo=timezone.utc),
                    "ticker": "TSLA", "source_id": "synthetic-fixture"}
        self.assertFalse(eligible_replay(
            CASES[0], alert_timestamp=alert, timestamped_bars=bars,
            signal_snapshot=snapshot,
            alert_evidence={"verified": True, "source_id": "synthetic-alert-fixture"},
            price_evidence={"verified": True, "source_id": "synthetic-bars-fixture"}))

    def test_wrong_ticker_blocks(self):
        alert = datetime(2026, 10, 22, 11, 33, tzinfo=timezone.utc)
        bars = [{"timestamp": datetime(2026, 10, 23, 20, tzinfo=timezone.utc),
                 "open": 100, "high": 105, "low": 99, "close": 103, "volume": 10000}]
        self.assertFalse(eligible_replay(
            CASES[0], alert_timestamp=alert, timestamped_bars=bars,
            signal_snapshot={"created_at": alert, "ticker": "META", "source_id": "fixture"},
            alert_evidence={"verified": True, "source_id": "fixture"},
            price_evidence={"verified": True, "source_id": "fixture"}))

if __name__ == "__main__":
    unittest.main()
