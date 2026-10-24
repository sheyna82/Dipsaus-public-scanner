"""Offline integration test for manual historical data acquisition.

Mocks HTTP entirely: no network, secrets, or real-market assertions.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research_event_stooq_acquisition import acquire_stooq_history

PAYLOAD = (b"Date,Open,High,Low,Close,Volume\n"
           b"2026-10-20,100,102,99,101,1000\n"
           b"2026-10-21,101,103,100,102,1500\n")


class MockResponse:
    def __init__(self, payload, url):
        self.payload = payload
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.payload[:limit]


class AcquisitionIntegrationTests(unittest.TestCase):
    def test_end_to_end_mocked_download_and_hash(self):
        def fake_open(url, timeout):
            self.assertIn("stooq.com", url)
            self.assertEqual(timeout, 15)
            return MockResponse(PAYLOAD, url)

        with tempfile.TemporaryDirectory() as folder:
            with patch("research_event_stooq_acquisition.urlopen", fake_open):
                result = acquire_stooq_history(
                    "AMD", "2026-10-20", "2026-10-21", folder,
                    allow_network=True)
            basename = "AMD_2026-10-20_2026-10-21"
            self.assertEqual((Path(folder) / (basename + ".csv")).read_bytes(), PAYLOAD)
            stored = json.loads((Path(folder) / (basename + ".json")).read_text())
            expected = hashlib.sha256(PAYLOAD).hexdigest()
            self.assertEqual(result["content_sha256"], expected)
            self.assertEqual(stored["content_sha256"], expected)
            self.assertEqual(result["row_count"], 2)
            self.assertFalse(result["trade_ready"])

    def test_redirect_outside_allowlist_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch("research_event_stooq_acquisition.urlopen",
                       return_value=MockResponse(PAYLOAD, "https://evil.example/prices")):
                with self.assertRaisesRegex(ValueError, "unexpected_redirect_host"):
                    acquire_stooq_history(
                        "AMD", "2026-10-20", "2026-10-21", folder,
                        allow_network=True)
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
