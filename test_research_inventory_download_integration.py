"""Synthetic API inventory -> existing downloader -> archive validation test.

No real GitHub network calls, live scanner changes, or secrets.
"""
import hashlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from research_immutable_candidate_registration import register_candidate_once
from research_prospective_archive import archive_ledger
from research_prospective_artifact_download import download_previous_archive
from research_registration_artifact_inventory import inventory_candidate_artifacts
from research_registration_archive_bridge import inspect_candidate_archive


class Response(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class InventoryToDownloadTests(unittest.TestCase):
    def test_inventory_to_verified_candidate_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = root / "candidates"
            outcomes = root / "outcomes"
            candidates.mkdir()
            outcomes.mkdir()
            register_candidate_once(
                {"symbol": "AMD", "signal_session": "2026-11-02",
                 "protocol_id": "v1", "trade_ready": False, "future_outcome": None},
                candidates, clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            inner_path = root / "inner.zip"
            archive_ledger(candidates, outcomes, inner_path)
            inner = inner_path.read_bytes()
            outer = io.BytesIO()
            with ZipFile(outer, "w") as z:
                z.writestr("prospective-ledger-synthetic.zip", inner)

            def mocked_github(request, timeout):
                if request.full_url.endswith("/actions/artifacts?per_page=100&page=1"):
                    return Response(json.dumps({"total_count": 1, "artifacts": [
                        {"id": 42, "name": "prospective-ledger-synthetic"}]}).encode())
                if request.full_url.endswith("/actions/artifacts/42/zip"):
                    return Response(outer.getvalue())
                raise AssertionError("unexpected_api_request")

            inventory = inventory_candidate_artifacts(
                "owner/repo", "fake-token", "prospective-ledger-synthetic",
                opener=mocked_github)
            self.assertTrue(inventory["metadata_inventory_exhausted"])
            self.assertEqual(inventory["artifact_ids"], [42])
            download = download_previous_archive(
                "owner/repo", "fake-token", inventory["artifact_ids"][0],
                root / "downloaded.zip",
                expected_sha256=hashlib.sha256(inner).hexdigest(),
                opener=mocked_github)
            self.assertTrue(download["expected_sha256_verified"])
            archive = inspect_candidate_archive(download["destination"])
            self.assertEqual(archive["candidate_count"], 1)
            self.assertFalse(archive["external_provenance_authenticated"])


if __name__ == "__main__":
    unittest.main()
