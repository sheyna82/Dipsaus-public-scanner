import unittest
from research_prospective_previous_run_selection import select_previous_artifact


class PreviousRunSelectionTests(unittest.TestCase):
    def test_only_unexpired_prior_run_is_selected(self):
        artifacts = [
            {"id": 1, "name": "ledger", "expired": False,
             "workflow_run": {"id": 12}, "created_at": "2026-10-25T09:00:00Z",
             "expires_at": "2026-11-01T09:00:00Z"},
            {"id": 2, "name": "ledger", "expired": False,
             "workflow_run": {"id": 13}, "created_at": "2026-10-25T10:00:00Z",
             "expires_at": "2026-11-01T10:00:00Z"},
            {"id": 3, "name": "ledger", "expired": True,
             "workflow_run": {"id": 11}, "created_at": "2026-10-25T11:00:00Z",
             "expires_at": "2026-11-01T11:00:00Z"}]
        result = select_previous_artifact(
            artifacts, current_run_id=13, artifact_name="ledger",
            now_iso="2026-10-25T12:00:00Z")
        self.assertEqual(result["selected_artifact_id"], 1)
        self.assertFalse(result["cross_run_restoration_performed"])

    def test_no_valid_artifact(self):
        result = select_previous_artifact(
            [{"id": 1, "name": "ledger", "expired": False,
              "workflow_run": {"id": 12}, "expires_at": "2026-10-24T00:00:00Z"}],
            current_run_id=13, artifact_name="ledger",
            now_iso="2026-10-25T12:00:00Z")
        self.assertIsNone(result["selected_artifact_id"])


    def test_pinned_run_and_commit_reject_wrong_identity(self):
        sha = "a" * 40
        artifacts = [
            {"id": 31, "name": "ledger", "expired": False,
             "workflow_run": {"id": 100, "head_sha": sha},
             "created_at": "2026-10-25T09:00:00Z",
             "expires_at": "2026-11-01T09:00:00Z"},
            {"id": 32, "name": "ledger", "expired": False,
             "workflow_run": {"id": 101, "head_sha": "b" * 40},
             "created_at": "2026-10-25T10:00:00Z",
             "expires_at": "2026-11-01T10:00:00Z"}]
        result = select_previous_artifact(
            artifacts, current_run_id=102, artifact_name="ledger",
            now_iso="2026-10-25T12:00:00Z",
            expected_source_run_id=100, expected_head_sha=sha)
        self.assertEqual(result["selected_artifact_id"], 31)
        self.assertIn("unexpected_source_run",
                      [item["reason"] for item in result["rejected"]])
        wrong_commit = select_previous_artifact(
            artifacts, current_run_id=102, artifact_name="ledger",
            now_iso="2026-10-25T12:00:00Z",
            expected_source_run_id=100, expected_head_sha="c" * 40)
        self.assertIsNone(wrong_commit["selected_artifact_id"])
        self.assertIn("unexpected_source_commit",
                      [item["reason"] for item in wrong_commit["rejected"]])

    def test_invalid_pinned_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_expected_source_run_id"):
            select_previous_artifact([], current_run_id=2,
                                     artifact_name="ledger",
                                     now_iso="2026-10-25T12:00:00Z",
                                     expected_source_run_id=-1)
        with self.assertRaisesRegex(ValueError, "invalid_expected_head_sha"):
            select_previous_artifact([], current_run_id=2,
                                     artifact_name="ledger",
                                     now_iso="2026-10-25T12:00:00Z",
                                     expected_head_sha="not-a-sha")

if __name__ == "__main__":
    unittest.main()
