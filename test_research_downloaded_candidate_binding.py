"""Synthetic end-to-end checks of downloaded artifact candidate binding."""
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
from research_downloaded_candidate_binding import verify_downloaded_candidate_binding


class DownloadedCandidateBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        candidates, outcomes = root / "candidates", root / "outcomes"
        candidates.mkdir()
        outcomes.mkdir()
        registered = register_candidate_once({
            "symbol": "TEST", "signal_session": "2026-11-02",
            "protocol_id": "research-v1", "trade_ready": False,
            "future_outcome": None,
        }, candidates, clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
        self.candidate = json.loads(Path(registered["path"]).read_text())
        inner_path = root / "candidate-archive.zip"
        archive_ledger(candidates, outcomes, inner_path)
        self.inner = inner_path.read_bytes()
        self.args = {
            "expected_run_id": 123,
            "expected_head_sha": "c" * 40,
            "expected_archive_sha256": hashlib.sha256(self.inner).hexdigest(),
        }
        self.build_outer(self.inner)

    def tearDown(self):
        self.tmp.cleanup()

    def build_outer(self, inner):
        stream = io.BytesIO()
        with ZipFile(stream, "w") as z:
            z.writestr("candidate-archive.zip", inner)
        self.outer = stream.getvalue()
        self.metadata = {
            "id": 456, "expired": False,
            "created_at": "2026-11-03T15:01:00Z",
            "digest": "sha256:" + hashlib.sha256(self.outer).hexdigest(),
            "workflow_run": {"id": 123, "head_sha": "c" * 40},
        }

    def check(self):
        return verify_downloaded_candidate_binding(
            self.outer, self.metadata, self.candidate, **self.args)

    def test_exact_downloaded_candidate_bound_without_prospectivity(self):
        result = self.check()
        self.assertTrue(result["candidate_in_downloaded_artifact_verified"])
        self.assertTrue(result["github_artifact_download_digest_verified"])
        self.assertFalse(result["prospective_signal_proven"])
        self.assertFalse(result["trade_ready"])

    def test_wrong_candidate_rejected(self):
        self.candidate["symbol"] = "OTHER"
        with self.assertRaises(ValueError):
            self.check()

    def test_wrong_github_digest_rejected(self):
        self.metadata["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "github_artifact_digest_mismatch"):
            self.check()

    def test_wrong_inner_archive_rejected(self):
        self.args["expected_archive_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "candidate_archive_digest_mismatch"):
            self.check()

    def test_modified_inner_archive_rejected_even_with_updated_transport_hashes(self):
        self.build_outer(self.inner + b"extra")
        self.args["expected_archive_sha256"] = hashlib.sha256(self.inner + b"extra").hexdigest()
        with self.assertRaises(ValueError):
            self.check()


if __name__ == "__main__":
    unittest.main()
