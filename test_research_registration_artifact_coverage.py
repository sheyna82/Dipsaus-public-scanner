import tempfile
import unittest
from datetime import datetime, timezone

from research_immutable_candidate_registration import register_candidate_once
from research_registration_artifact_coverage import audit_registration_run_coverage


class ArtifactCoverageTests(unittest.TestCase):
    def receipt(self, run_id, paths):
        return {"run_id": run_id, "artifact_verified": True,
                "artifact_complete": True, "candidate_paths": paths}

    def test_missing_declared_run_is_not_complete(self):
        result = audit_registration_run_coverage([self.receipt(1, [])], [1, 2])
        self.assertEqual(result["status"], "missing_declared_runs")
        self.assertEqual(result["missing_run_ids"], [2])

    def test_declared_runs_reconciled_without_claiming_global_completeness(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = {"symbol": "AMD", "signal_session": "2026-11-02",
                         "protocol_id": "v1", "future_outcome": None, "trade_ready": False}
            registered = register_candidate_once(candidate, tmp,
                clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            result = audit_registration_run_coverage(
                [self.receipt(1, [registered["path"]]), self.receipt(2, [])], [1, 2])
            self.assertEqual(result["candidate_count"], 1)
            self.assertFalse(result["run_set_independently_complete"])
            self.assertFalse(result["artifact_authentication_independent"])

    def test_duplicate_run_receipt_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_run_receipt"):
            audit_registration_run_coverage([self.receipt(1, []), self.receipt(1, [])], [1])

    def test_unverified_receipt_rejected(self):
        bad = self.receipt(1, [])
        bad["artifact_verified"] = False
        with self.assertRaisesRegex(ValueError, "unverified_artifact_receipt"):
            audit_registration_run_coverage([bad], [1])


if __name__ == "__main__":
    unittest.main()
