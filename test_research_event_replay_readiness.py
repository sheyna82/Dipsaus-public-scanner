import unittest
from datetime import datetime, timezone
from research_event_replay_readiness import audit_all, audit_case
from research_event_replay_intake_202610 import CASES

class EventReadinessTests(unittest.TestCase):
    def test_missing_evidence_reported_for_all_four(self):
        reports = audit_all()
        self.assertEqual(len(reports), 4)
        for report in reports:
            self.assertEqual(len(report["missing_evidence"]), 5)
            self.assertFalse(report["performance_claim_allowed"])
            self.assertFalse(report["intake_eligible"])

    def test_unknown_case_rejected(self):
        with self.assertRaises(ValueError):
            audit_case({"ticker": "FAKE"})

    def test_complete_metadata_does_not_prove_authenticity(self):
        alert = datetime(2026, 10, 22, 11, 33, tzinfo=timezone.utc)
        evidence = {
            "alert_timestamp": alert,
            "timestamped_bars": [{"timestamp": datetime(2026, 10, 23, 20, tzinfo=timezone.utc),
                                  "open": 100, "high": 105, "low": 99, "close": 103, "volume": 10000}],
            "signal_snapshot": {"created_at": alert, "ticker": "TSLA", "source_id": "fixture",
                                "origin": "independent_archive"},
            "alert_evidence": {"verified": True, "source_id": "fixture", "origin": "independent_archive"},
            "price_evidence": {"verified": True, "source_id": "fixture", "origin": "independent_archive"},
        }
        report = audit_case(CASES[0], evidence)
        self.assertTrue(report["intake_eligible"])
        self.assertFalse(report["independently_authenticated"])
        self.assertFalse(report["performance_claim_allowed"])

if __name__ == "__main__":
    unittest.main()
