"""Isolated transport regression tests; synthetic bytes only."""
import hashlib
import io
import unittest
from zipfile import ZipFile

from research_real_candidate_artifact_verifier import verify_real_candidate_artifact


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.inner = b"synthetic test archive"
        stream = io.BytesIO()
        with ZipFile(stream, "w") as archive:
            archive.writestr("candidate-archive.zip", self.inner)
        self.outer = stream.getvalue()
        self.meta = {
            "id": 456, "expired": False,
            "digest": "sha256:" + hashlib.sha256(self.outer).hexdigest(),
            "workflow_run": {"id": 123, "head_sha": "c" * 40},
        }
        self.args = {
            "expected_run_id": 123,
            "expected_head_sha": "c" * 40,
            "expected_archive_sha256": hashlib.sha256(self.inner).hexdigest(),
            "expected_candidate_identity_sha256": "a" * 64,
        }

    def check(self):
        return verify_real_candidate_artifact(self.outer, self.meta, **self.args)

    def test_transport_verified_not_candidate(self):
        result = self.check()
        self.assertTrue(result["candidate_archive_sha256_verified"])
        self.assertFalse(result["candidate_identity_in_archive_verified"])
        self.assertFalse(result["trade_ready"])

    def test_wrong_run_rejected(self):
        self.args["expected_run_id"] = 124
        with self.assertRaisesRegex(ValueError, "github_run_identity_mismatch"):
            self.check()

    def test_wrong_outer_digest_rejected(self):
        self.meta["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "github_artifact_digest_mismatch"):
            self.check()

    def test_wrong_inner_digest_rejected(self):
        self.args["expected_archive_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "candidate_archive_digest_mismatch"):
            self.check()

    def test_expired_rejected(self):
        self.meta["expired"] = True
        with self.assertRaisesRegex(ValueError, "artifact_unavailable"):
            self.check()


if __name__ == "__main__":
    unittest.main()
