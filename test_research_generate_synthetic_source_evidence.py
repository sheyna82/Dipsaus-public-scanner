import hashlib
import tempfile
import unittest
from pathlib import Path

from research_generate_synthetic_source_evidence import generate
from research_source_evidence_archive import verify_source_evidence_archive


class SyntheticSourceEvidenceGenerationTests(unittest.TestCase):
    def test_generates_source_bytes_and_verifiable_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = generate(root)
            archive = root / "source-evidence-synthetic.zip"
            self.assertTrue(archive.is_file())
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), result["sha256"])
            self.assertEqual((root / "sha256.txt").read_text(),
                             result["sha256"] + "  source-evidence-synthetic.zip\n")
            self.assertFalse(result["trade_ready"])
            verified = verify_source_evidence_archive(archive)
            self.assertFalse(verified["independent_source_authentication"])


if __name__ == "__main__":
    unittest.main()
