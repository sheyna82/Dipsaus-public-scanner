import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from research_compare_omxh25_actual_issuer_yahoo import compare_archive

def archive_with(issuer, yahoo):
    directory = tempfile.TemporaryDirectory()
    path = Path(directory.name) / "observation.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("omxh25-history-post-raw-unverified.json", json.dumps(issuer))
        archive.writestr("europe-benchmarks.json", json.dumps(yahoo))
    return directory, path

class ComparisonTests(unittest.TestCase):
    def test_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("other.json", "{}")
            with self.assertRaisesRegex(ValueError, "MISSING_DUPLICATE"):
                compare_archive(path)

    def test_invalid_yahoo_gates_rejected(self):
        issuer = {}
        yahoo = {"research_only": True, "trade_ready": True, "benchmark_identity_verified": False}
        directory, path = archive_with(issuer, yahoo)
        with directory:
            with patch("research_compare_omxh25_actual_issuer_yahoo.validate", return_value={"records": [], "source_sha256": "test"}):
                with self.assertRaisesRegex(ValueError, "UNSAFE_YAHOO_GATES"):
                    compare_archive(path)

    def test_missing_yahoo_symbol_rejected(self):
        issuer = {}
        yahoo = {"research_only": True, "trade_ready": False, "benchmark_identity_verified": False, "series": {}}
        directory, path = archive_with(issuer, yahoo)
        with directory:
            with patch("research_compare_omxh25_actual_issuer_yahoo.validate", return_value={"records": [], "source_sha256": "test"}):
                with self.assertRaisesRegex(ValueError, "INVALID_YAHOO_SYMBOL"):
                    compare_archive(path)

if __name__ == "__main__":
    unittest.main()
