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

    def test_missing_issuer_session_rejected(self):
        import base64
        import hashlib
        raw = b"sample-yahoo-response"
        yahoo = {
            "research_only": True, "trade_ready": False, "benchmark_identity_verified": False,
            "series": {"OMXH25": {
                "provider_symbol": "^OMXH25",
                "provider_metadata": {"currency": "EUR", "instrumentType": "INDEX"},
                "source_raw_base64": base64.b64encode(raw).decode("ascii"),
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "bars": []
            }}
        }
        directory, path = archive_with({}, yahoo)
        with directory:
            with patch("research_compare_omxh25_actual_issuer_yahoo.validate",
                       return_value={"records": [{"date": "2026-11-05", "value": 6254.3}], "source_sha256": "test"}):
                with self.assertRaisesRegex(ValueError, "MISSING_YAHOO_SESSION"):
                    compare_archive(path)

    def test_invalid_currency_rejected(self):
        yahoo = {
            "research_only": True, "trade_ready": False, "benchmark_identity_verified": False,
            "series": {"OMXH25": {"provider_symbol": "^OMXH25",
                                  "provider_metadata": {"currency": "USD", "instrumentType": "INDEX"}}}
        }
        directory, path = archive_with({}, yahoo)
        with directory:
            with patch("research_compare_omxh25_actual_issuer_yahoo.validate",
                       return_value={"records": [], "source_sha256": "test"}):
                with self.assertRaisesRegex(ValueError, "INVALID_YAHOO_METADATA"):
                    compare_archive(path)

    def test_mismatched_close_rejected(self):
        import base64
        import hashlib
        from datetime import datetime, timezone
        raw = b"fixture-yahoo-response"
        timestamp = int(datetime(2026, 11, 5, 16, tzinfo=timezone.utc).timestamp())
        yahoo = {
            "research_only": True, "trade_ready": False, "benchmark_identity_verified": False,
            "series": {"OMXH25": {
                "provider_symbol": "^OMXH25",
                "provider_metadata": {"currency": "EUR", "instrumentType": "INDEX"},
                "source_raw_base64": base64.b64encode(raw).decode("ascii"),
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "bars": [{"t": timestamp, "close": 6200.0}]
            }}
        }
        directory, path = archive_with({}, yahoo)
        with directory:
            with patch("research_compare_omxh25_actual_issuer_yahoo.validate",
                       return_value={"records": [{"date": "2026-11-05", "value": 6254.3}], "source_sha256": "test"}):
                with self.assertRaisesRegex(ValueError, "CLOSE_MISMATCH"):
                    compare_archive(path)

if __name__ == "__main__":
    unittest.main()
