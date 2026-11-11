import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from research_generate_synthetic_source_evidence import generate
from research_github_source_evidence_verifier import verify_github_source_evidence


class GithubSourceEvidenceVerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        generate(root)
        buf = io.BytesIO()
        with ZipFile(buf, "w") as z:
            z.write(root / "source-evidence-synthetic.zip", "source-evidence-synthetic.zip")
            z.write(root / "sha256.txt", "sha256.txt")
        self.outer = buf.getvalue()
        self.metadata = {
            "id": 123, "name": "dipsaus-source-bytes-synthetic-evidence",
            "expired": False, "digest": "sha256:" + hashlib.sha256(self.outer).hexdigest(),
            "workflow_run": {"id": 456, "head_sha": "a" * 40},
        }

    def tearDown(self):
        self.tmp.cleanup()

    def verify(self):
        return verify_github_source_evidence(self.outer, self.metadata,
                                             expected_run_id=456, expected_head_sha="a" * 40)

    def test_complete_transport_is_verified_but_not_market_authenticated(self):
        result = self.verify()
        self.assertEqual(result["status"], "github_synthetic_source_bytes_verified")
        self.assertFalse(result["prospective_stock_registration_verified"])
        self.assertFalse(result["trade_ready"])

    def test_outer_tampering_rejected(self):
        self.outer += b"x"
        with self.assertRaisesRegex(ValueError, "github_artifact_digest_mismatch"):
            self.verify()

    def test_wrong_run_rejected(self):
        self.metadata["workflow_run"]["id"] = 999
        with self.assertRaisesRegex(ValueError, "github_run_identity_mismatch"):
            self.verify()

    def test_wrong_artifact_type_rejected(self):
        self.metadata["name"] = "unrelated"
        with self.assertRaisesRegex(ValueError, "unexpected_or_expired_artifact"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
