"""Regression checks for real GitHub API artifact digest boundary."""
import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from research_github_synthetic_artifact_verifier import verify_github_synthetic_artifact
from research_prospective_archive import archive_ledger


class GitHubArtifactVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        (root / "candidates").mkdir()
        (root / "outcomes").mkdir()
        inner = root / "source.zip"
        archive_ledger(root / "candidates", root / "outcomes", inner)
        raw = inner.read_bytes()
        outer = io.BytesIO()
        with ZipFile(outer, "w") as archive:
            archive.writestr("prospective-ledger-synthetic.zip", raw)
            archive.writestr("sha256.txt", hashlib.sha256(raw).hexdigest() + "  prospective-ledger-synthetic.zip\n")
        self.payload = outer.getvalue()
        self.metadata = {
            "id": 1234, "expired": False,
            "digest": "sha256:" + hashlib.sha256(self.payload).hexdigest(),
            "workflow_run": {"id": 5678, "head_sha": "a" * 40},
        }
        self.destination = root / "restored.zip"

    def tearDown(self):
        self.temp.cleanup()

    def verify(self):
        return verify_github_synthetic_artifact(
            self.payload, self.metadata, self.destination,
            expected_run_id=5678, expected_head_sha="a" * 40)

    def test_complete_digest_and_manifest_validation(self):
        result = self.verify()
        self.assertTrue(result["external_github_artifact_digest_verified"])
        self.assertFalse(result["prospective_stock_registration_verified"])
        self.assertFalse(result["trade_ready"])

    def test_modified_outer_bytes_rejected_before_writing(self):
        self.payload += b"tamper"
        with self.assertRaisesRegex(ValueError, "github_artifact_digest_mismatch"):
            self.verify()
        self.assertFalse(self.destination.exists())

    def test_wrong_run_rejected(self):
        self.metadata["workflow_run"]["id"] = 9999
        with self.assertRaisesRegex(ValueError, "github_run_identity_mismatch"):
            self.verify()

    def test_wrong_head_rejected(self):
        self.metadata["workflow_run"]["head_sha"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "github_run_identity_mismatch"):
            self.verify()

    def test_missing_digest_rejected(self):
        self.metadata.pop("digest")
        with self.assertRaisesRegex(ValueError, "missing_github_digest"):
            self.verify()

    def test_expired_artifact_rejected(self):
        self.metadata["expired"] = True
        with self.assertRaisesRegex(ValueError, "artifact_unavailable"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
