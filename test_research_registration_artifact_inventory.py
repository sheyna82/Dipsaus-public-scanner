import io
import json
import unittest

from research_registration_artifact_inventory import inventory_candidate_artifacts


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class ArtifactInventoryTests(unittest.TestCase):
    def opener(self, pages):
        def open_page(request, timeout):
            page = int(request.full_url.split("page=")[-1])
            return FakeResponse(json.dumps({"total_count": sum(len(p) for p in pages), "artifacts": pages[page - 1]}).encode())
        return open_page

    def test_short_page_proves_only_pagination_exhaustion(self):
        report = inventory_candidate_artifacts("owner/repo", "fake-token", "signals",
            opener=self.opener([[{"id": 10, "name": "signals"}]]))
        self.assertTrue(report["metadata_inventory_exhausted"])
        self.assertFalse(report["historical_run_coverage_proven"])
        self.assertEqual(report["artifact_ids"], [10])

    def test_full_page_at_limit_is_incomplete(self):
        page = [{"id": i + 1, "name": "signals"} for i in range(100)]
        report = inventory_candidate_artifacts("owner/repo", "fake-token", "signals",
            opener=self.opener([page]), max_pages=1)
        self.assertEqual(report["status"], "metadata_pages_exhausted")
        self.assertTrue(report["metadata_inventory_exhausted"])

    def test_full_page_at_limit_with_more_pages_is_incomplete(self):
        page = [{"id": i + 1, "name": "signals"} for i in range(100)]
        def opener(request, timeout):
            return FakeResponse(json.dumps({"total_count": 101, "artifacts": page}).encode())
        report = inventory_candidate_artifacts("owner/repo", "fake-token", "signals",
            opener=opener, max_pages=1)
        self.assertEqual(report["status"], "pagination_limit_reached")
        self.assertFalse(report["metadata_inventory_exhausted"])

    def test_duplicate_artifact_id_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_or_duplicate_artifact_ids"):
            inventory_candidate_artifacts("owner/repo", "fake-token", "signals",
                opener=self.opener([[{"id": 1, "name": "signals"},
                                    {"id": 1, "name": "signals"}]]))

    def test_github_total_count_mismatch_rejected(self):
        def opener(request, timeout):
            return FakeResponse(json.dumps({"total_count": 5, "artifacts": [
                {"id": 1, "name": "signals"}]}).encode())
        with self.assertRaisesRegex(ValueError, "artifact_inventory_count_mismatch"):
            inventory_candidate_artifacts("owner/repo", "fake-token", "signals",
                                          opener=opener)

    def test_missing_token_rejected(self):
        with self.assertRaisesRegex(ValueError, "github_token_required"):
            inventory_candidate_artifacts("owner/repo", "", "signals")


if __name__ == "__main__":
    unittest.main()
