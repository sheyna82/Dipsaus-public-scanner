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


if __name__ == "__main__":
    unittest.main()
