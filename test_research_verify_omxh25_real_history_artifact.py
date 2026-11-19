import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from test_research_validate_omxh25_real_history_post import fixture
from research_verify_omxh25_real_history_artifact import verify_archive, MEMBER

class ArtifactTests(unittest.TestCase):
    def test_offline_zip_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(MEMBER, json.dumps(fixture()))
            result = verify_archive(path)
            self.assertEqual(result["record_count"], 1)
            self.assertFalse(result["trade_ready"])

    def test_missing_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("other.json", "{}")
            with self.assertRaisesRegex(ValueError, "MISSING_OR_DUPLICATE"):
                verify_archive(path)

    def test_duplicate_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(MEMBER, json.dumps(fixture()))
                archive.writestr(MEMBER, json.dumps(fixture()))
            with self.assertRaisesRegex(ValueError, "MISSING_OR_DUPLICATE"):
                verify_archive(path)

if __name__ == "__main__":
    unittest.main()
