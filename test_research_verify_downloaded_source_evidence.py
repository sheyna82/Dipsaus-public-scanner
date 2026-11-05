import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from zipfile import ZipFile

from research_generate_synthetic_source_evidence import generate
from research_verify_downloaded_source_evidence import main


class DownloadedSourceEvidenceCLITests(unittest.TestCase):
    def test_cli_verifies_independent_metadata_and_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generate(root)
            outer = root / "github-artifact.zip"
            with ZipFile(outer, "w") as z:
                z.write(root / "source-evidence-synthetic.zip", "source-evidence-synthetic.zip")
                z.write(root / "sha256.txt", "sha256.txt")
            metadata = root / "metadata.json"
            metadata.write_text(json.dumps({
                "id": 123, "name": "dipsaus-source-bytes-synthetic-evidence",
                "expired": False,
                "digest": "sha256:" + hashlib.sha256(outer.read_bytes()).hexdigest(),
                "workflow_run": {"id": 456, "head_sha": "a" * 40},
            }))
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main([
                    "--artifact-zip", str(outer),
                    "--metadata-json", str(metadata),
                    "--expected-run-id", "456",
                    "--expected-head-sha", "a" * 40,
                ]), 0)
            report = json.loads(output.getvalue())
            self.assertTrue(report["external_github_artifact_digest_verified"])
            self.assertFalse(report["prospective_stock_registration_verified"])
            self.assertFalse(report["trade_ready"])


if __name__ == "__main__":
    unittest.main()
