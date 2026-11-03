"""Fail-closed tests for prospective receipt metadata."""
import unittest
from research_registration_receipt_gate import audit_registration_receipt


class ReceiptGateTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {
            "research_only": True, "trade_ready": False, "future_outcome": None,
            "registration_clock_proof_independent": False,
            "protocol_id": "research-v1", "symbol": "TEST", "signal_session": "2026-11-02",
            "candidate_identity_sha256": "a" * 64,
            "registered_at_utc": "2026-11-03T15:00:00+00:00",
        }
        self.artifact = {
            "id": 789, "expired": False, "created_at": "2026-11-03T15:01:00Z",
            "digest": "sha256:" + "b" * 64,
            "workflow_run": {"id": 123, "head_sha": "c" * 40},
        }

    def audit(self):
        return audit_registration_receipt(
            self.candidate, self.artifact, expected_run_id=123, expected_head_sha="c" * 40)

    def test_valid_metadata_never_claims_candidate_verified(self):
        result = self.audit()
        self.assertEqual(result["status"], "receipt_metadata_consistent")
        self.assertFalse(result["candidate_in_artifact_verified"])
        self.assertFalse(result["independent_pre_signal_timestamp_proof"])
        self.assertFalse(result["trade_ready"])

    def test_late_github_receipt_is_not_prospective(self):
        result = self.audit()
        self.assertEqual(result["receipt_timing_classification"],
                         "artifact_created_after_signal_session_not_prospective_for_that_session")
        self.assertFalse(result["prospective_signal_proven"])

    def test_same_day_github_receipt_still_requires_proof(self):
        self.candidate["signal_session"] = "2026-11-03"
        result = self.audit()
        self.assertEqual(result["receipt_timing_classification"],
                         "same_day_receipt_requires_exchange_cutoff_and_input_proof")
        self.assertFalse(result["prospective_signal_proven"])

    def test_artifact_predates_local_registration_rejected(self):
        self.artifact["created_at"] = "2026-11-03T14:59:59Z"
        with self.assertRaisesRegex(ValueError, "artifact_predates_local_registration"):
            self.audit()

    def test_wrong_run_rejected(self):
        self.artifact["workflow_run"]["id"] = 124
        with self.assertRaisesRegex(ValueError, "artifact_provenance_mismatch"):
            self.audit()

    def test_wrong_head_rejected(self):
        self.artifact["workflow_run"]["head_sha"] = "d" * 40
        with self.assertRaisesRegex(ValueError, "artifact_provenance_mismatch"):
            self.audit()

    def test_missing_digest_rejected(self):
        self.artifact.pop("digest")
        with self.assertRaisesRegex(ValueError, "invalid_artifact_digest"):
            self.audit()

    def test_future_outcome_rejected(self):
        self.candidate["future_outcome"] = {"return": 1}
        with self.assertRaisesRegex(ValueError, "future_outcome_present"):
            self.audit()

    def test_local_clock_claim_cannot_be_marked_independent(self):
        self.candidate["registration_clock_proof_independent"] = True
        with self.assertRaisesRegex(ValueError, "unsupported_independent_clock_claim"):
            self.audit()

    def test_naive_timestamp_rejected(self):
        self.candidate["registered_at_utc"] = "2026-11-03T15:00:00"
        with self.assertRaisesRegex(ValueError, "timezone_required"):
            self.audit()


if __name__ == "__main__":
    unittest.main()
