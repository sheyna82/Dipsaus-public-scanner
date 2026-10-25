import io
import json
import unittest
from research_prospective_artifact_discovery import discover_previous_archive


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class ArtifactDiscoveryTests(unittest.TestCase):
    def test_read_only_metadata_selection(self):
        requested = []
        def fake_open(request, timeout):
            requested.append(request.full_url)
            payload = {"artifacts": [{
                "id": 17, "name": "ledger", "expired": False,
                "workflow_run": {"id": 44},
                "created_at": "2026-10-24T10:00:00Z",
                "expires_at": "2026-10-31T10:00:00Z"}]}
            return FakeResponse(json.dumps(payload).encode())
        result = discover_previous_archive(
            "sheyna82/Dipsaus-public-scanner", "placeholder-test-token", 45,
            "ledger", "2026-10-25T10:00:00Z", opener=fake_open)
        self.assertEqual(result["selected_artifact_id"], 17)
        self.assertEqual(result["metadata_pages_checked"], 1)
        self.assertFalse(result["cross_run_restoration_performed"])
        self.assertEqual(len(requested), 1)

    def test_reject_missing_credentials(self):
        with self.assertRaisesRegex(ValueError, "github_token_required"):
            discover_previous_archive("a/b", "", 1, "ledger",
                                      "2026-10-25T10:00:00Z")


if __name__ == "__main__":
    unittest.main()
