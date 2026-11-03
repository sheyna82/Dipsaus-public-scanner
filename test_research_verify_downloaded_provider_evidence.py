"""Regression tests for downloaded synthetic provider evidence."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from research_generate_synthetic_provider_evidence import generate
from research_verify_downloaded_provider_evidence import verify_downloaded_provider_artifact, main


class DownloadedProviderEvidenceTests(unittest.TestCase):
    def make_outer(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        generate(root)
        buf = io.BytesIO()
        with ZipFile(buf, "w", ZIP_DEFLATED) as z:
            z.write(root / "synthetic-provider-evidence.zip", "synthetic-provider-evidence.zip")
            z.write(root / "sha256.txt", "sha256.txt")
        return buf.getvalue()

    def test_valid_roundtrip(self):
        result = verify_downloaded_provider_artifact(self.make_outer())
        self.assertTrue(result["synthetic_data_only"])
        self.assertFalse(result["trade_ready"])

    def test_cli_reads_downloaded_artifact(self):
        from contextlib import redirect_stdout
        output = io.StringIO()
        payload = self.make_outer()
        artifact = Path(self.temp.name) / "downloaded.zip"
        artifact.write_bytes(payload)
        with redirect_stdout(output):
            self.assertEqual(main(["--artifact-zip", str(artifact)]), 0)
        self.assertFalse(json.loads(output.getvalue())["trade_ready"])

    def test_rejects_oversized_outer_member_without_decompressing(self):
        buf = io.BytesIO()
        with ZipFile(buf, "w", ZIP_DEFLATED) as z:
            z.writestr("synthetic-provider-evidence.zip", b"x" * 5_000_001)
            z.writestr("sha256.txt", b"0" * 64)
        with self.assertRaisesRegex(ValueError, "oversized_artifact_member"):
            verify_downloaded_provider_artifact(buf.getvalue())

    def test_tampered_checksum_rejected(self):
        original = self.make_outer()
        with ZipFile(io.BytesIO(original)) as z:
            archive = z.read("synthetic-provider-evidence.zip")
        buf = io.BytesIO()
        with ZipFile(buf, "w", ZIP_DEFLATED) as z:
            z.writestr("synthetic-provider-evidence.zip", archive)
            z.writestr("sha256.txt", "0" * 64 + "  synthetic-provider-evidence.zip\n")
        with self.assertRaisesRegex(ValueError, "artifact_checksum_mismatch"):
            verify_downloaded_provider_artifact(buf.getvalue())


if __name__ == "__main__":
    unittest.main()
