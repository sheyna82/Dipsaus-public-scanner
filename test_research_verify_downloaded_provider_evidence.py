"""Regression tests for downloaded synthetic provider evidence."""
import io
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from research_generate_synthetic_provider_evidence import generate
from research_verify_downloaded_provider_evidence import verify_downloaded_provider_artifact


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
