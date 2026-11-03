"""Exercise the existing PR62 artifact downloader with a mocked HTTP response."""
import hashlib
import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from research_immutable_candidate_registration import register_candidate_once
from research_prospective_archive import archive_ledger
from research_prospective_artifact_download import download_previous_archive
from research_registration_archive_bridge import inspect_candidate_archive


class Response(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class ActualDownloaderIntegrationTests(unittest.TestCase):
    def test_existing_downloader_roundtrip_with_pinned_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates, outcomes = root / "candidates", root / "outcomes"
            candidates.mkdir()
            outcomes.mkdir()
            register_candidate_once({
                "symbol": "AMD", "signal_session": "2026-11-02",
                "protocol_id": "v1", "future_outcome": None, "trade_ready": False
            }, candidates, clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            inner_path = root / "source.zip"
            archive_ledger(candidates, outcomes, inner_path)
            inner = inner_path.read_bytes()
            outer = io.BytesIO()
            with ZipFile(outer, "w") as z:
                z.writestr("prospective-ledger-synthetic.zip", inner)
            dest = root / "downloaded.zip"
            result = download_previous_archive(
                "owner/repo", "fake-token", 42, dest,
                expected_sha256=hashlib.sha256(inner).hexdigest(),
                opener=lambda request, timeout: Response(outer.getvalue()))
            self.assertTrue(result["expected_sha256_verified"])
            summary = inspect_candidate_archive(dest)
            self.assertEqual(summary["candidate_count"], 1)
            self.assertFalse(summary["external_provenance_authenticated"])

    def test_existing_downloader_rejects_wrong_digest_without_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            outer = io.BytesIO()
            with ZipFile(outer, "w") as z:
                z.writestr("prospective-ledger-synthetic.zip", b"invalid")
            dest = Path(tmp) / "downloaded.zip"
            with self.assertRaisesRegex(ValueError, "artifact_expected_sha256_mismatch"):
                download_previous_archive("owner/repo", "fake-token", 42, dest,
                    expected_sha256="0" * 64,
                    opener=lambda request, timeout: Response(outer.getvalue()))
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
