"""Additional independent-provenance intake tests (synthetic test values only)."""
import unittest
from datetime import datetime, timezone
from research_event_replay_intake_202610 import CASES, eligible_replay

class IndependentEvidenceGateTests(unittest.TestCase):
    def test_complete_independent_metadata_can_pass_intake(self):
        alert = datetime(2026, 10, 22, 11, 33, tzinfo=timezone.utc)
        bars = [{"timestamp": datetime(2026, 10, 23, 20, tzinfo=timezone.utc),
                 "open": 100, "high": 105, "low": 99, "close": 103, "volume": 10000}]
        evidence = {"verified": True, "source_id": "example-archive", "origin": "independent_archive"}
        snapshot = {"created_at": alert, "ticker": "TSLA", "source_id": "example-signal",
                    "origin": "independent_archive"}
        self.assertTrue(eligible_replay(CASES[0], alert_timestamp=alert,
            timestamped_bars=bars, signal_snapshot=snapshot,
            alert_evidence=evidence, price_evidence=evidence))

    def test_unverified_origin_rejected(self):
        alert = datetime(2026, 10, 22, 11, 33, tzinfo=timezone.utc)
        bars = [{"timestamp": datetime(2026, 10, 23, 20, tzinfo=timezone.utc),
                 "open": 100, "high": 105, "low": 99, "close": 103, "volume": 10000}]
        evidence = {"verified": True, "source_id": "example", "origin": "synthetic"}
        snapshot = {"created_at": alert, "ticker": "TSLA", "source_id": "example",
                    "origin": "synthetic"}
        self.assertFalse(eligible_replay(CASES[0], alert_timestamp=alert,
            timestamped_bars=bars, signal_snapshot=snapshot,
            alert_evidence=evidence, price_evidence=evidence))

if __name__ == "__main__":
    unittest.main()
