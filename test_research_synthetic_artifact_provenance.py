"""Regression checks for GitHub metadata versus internal synthetic claims."""
import unittest
from research_synthetic_artifact_provenance import reconcile_synthetic_artifact

HEAD = "a" * 40
CHECKOUT = "b" * 40


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "synthetic_data_only": True, "research_only": True,
            "trade_ready": False, "future_outcome": None,
            "github_run_id_claimed": "123",
            "workflow_checkout_sha_claimed": CHECKOUT,
        }
        self.artifact = {
            "id": 456, "expired": False, "digest": "sha256:" + "c" * 64,
            "workflow_run": {"id": 123, "head_sha": HEAD},
        }

    def check(self):
        return reconcile_synthetic_artifact(
            self.record, self.artifact, expected_run_id=123, expected_head_sha=HEAD)

    def test_matching_github_metadata_preserves_unverified_boundaries(self):
        result = self.check()
        self.assertEqual(result["status"], "github_metadata_reconciled")
        self.assertFalse(result["workflow_checkout_authenticated"])
        self.assertFalse(result["download_digest_verified"])
        self.assertFalse(result["trade_ready"])
        self.assertEqual(result["registered_stock_candidates"], 0)

    def test_old_checkout_field_is_supported(self):
        self.record["head_sha_claimed"] = self.record.pop("workflow_checkout_sha_claimed")
        self.assertEqual(self.check()["artifact_id"], 456)

    def test_forged_run_claim_rejected(self):
        self.record["github_run_id_claimed"] = "999"
        with self.assertRaisesRegex(ValueError, "run_claim_mismatch"):
            self.check()

    def test_wrong_artifact_run_rejected(self):
        self.artifact["workflow_run"]["id"] = 999
        with self.assertRaisesRegex(ValueError, "artifact_run_mismatch"):
            self.check()

    def test_wrong_head_rejected(self):
        self.artifact["workflow_run"]["head_sha"] = "d" * 40
        with self.assertRaisesRegex(ValueError, "artifact_head_mismatch"):
            self.check()

    def test_missing_digest_rejected(self):
        self.artifact.pop("digest")
        with self.assertRaisesRegex(ValueError, "invalid_artifact_digest"):
            self.check()

    def test_expired_artifact_rejected(self):
        self.artifact["expired"] = True
        with self.assertRaisesRegex(ValueError, "artifact_expired_or_unknown"):
            self.check()

    def test_non_synthetic_candidate_rejected(self):
        self.record["synthetic_data_only"] = False
        with self.assertRaisesRegex(ValueError, "not_synthetic_research"):
            self.check()

    def test_invalid_checkout_claim_rejected(self):
        self.record["workflow_checkout_sha_claimed"] = "invalid"
        with self.assertRaisesRegex(ValueError, "invalid_checkout_claim"):
            self.check()


if __name__ == "__main__":
    unittest.main()
