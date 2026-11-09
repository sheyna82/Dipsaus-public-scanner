"""Offline disaster recovery safety tests: no network and no source fallback."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from research_recover_omxh25_offline import recover


class RecoveryTests(unittest.TestCase):
    def test_missing_retained_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(FileNotFoundError):
                recover(root/"missing.zip", root/"derived.zip", root/"receipt.json")
            self.assertFalse((root/"receipt.json").exists())

    def test_tampered_retained_source_fails_before_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root/"retained.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("payload", "untrusted")
            with self.assertRaisesRegex(ValueError, "CAPTURE_ARTIFACT_HASH_MISMATCH"):
                recover(source, root/"derived.zip", root/"receipt.json")
            self.assertFalse((root/"derived.zip").exists())
            self.assertFalse((root/"receipt.json").exists())

    def test_receipt_must_not_overwrite_original(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root/"original.zip"
            source.write_bytes(b"source")
            with self.assertRaisesRegex(ValueError, "RECEIPT_PATH_COLLISION"):
                recover(source, root/"derived.zip", source)
            self.assertEqual(source.read_bytes(), b"source")

    def test_receipt_must_not_overwrite_derived_archive(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaisesRegex(ValueError, "RECEIPT_PATH_COLLISION"):
                recover(root/"source.zip", root/"derived.zip", root/"derived.zip")


if __name__ == "__main__":
    unittest.main()
