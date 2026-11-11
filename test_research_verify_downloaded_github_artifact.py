import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from research_prospective_archive import archive_ledger
from research_verify_downloaded_github_artifact import main


class DownloadedArtifactCliTests(unittest.TestCase):
    def test_read_only_cli_verifies_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "candidates").mkdir()
            (root / "outcomes").mkdir()
            inner = root / "inner.zip"
            archive_ledger(root / "candidates", root / "outcomes", inner)
            raw = inner.read_bytes()
            outer = root / "artifact.zip"
            with ZipFile(outer, "w") as z:
                z.writestr("prospective-ledger-synthetic.zip", raw)
                z.writestr("sha256.txt", hashlib.sha256(raw).hexdigest() + "  prospective-ledger-synthetic.zip\n")
            metadata = root / "metadata.json"
            metadata.write_text(json.dumps({
                "id": 42, "expired": False,
                "digest": "sha256:" + hashlib.sha256(outer.read_bytes()).hexdigest(),
                "workflow_run": {"id": 99, "head_sha": "a" * 40}
            }))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--artifact-zip", str(outer), "--metadata-json", str(metadata),
                             "--expected-run-id", "99", "--expected-head-sha", "a" * 40])
            self.assertEqual(code, 0)
            result = json.loads(output.getvalue())
            self.assertTrue(result["external_github_artifact_digest_verified"])
            self.assertFalse(result["trade_ready"])

    def test_cli_wrong_head_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outer = root / "artifact.zip"
            outer.write_bytes(b"not-an-artifact")
            metadata = root / "metadata.json"
            metadata.write_text(json.dumps({
                "id": 42, "expired": False,
                "digest": "sha256:" + hashlib.sha256(outer.read_bytes()).hexdigest(),
                "workflow_run": {"id": 99, "head_sha": "a" * 40}
            }))
            with self.assertRaisesRegex(ValueError, "github_run_identity_mismatch"):
                main(["--artifact-zip", str(outer), "--metadata-json", str(metadata),
                      "--expected-run-id", "99", "--expected-head-sha", "b" * 40])


if __name__ == "__main__":
    unittest.main()
