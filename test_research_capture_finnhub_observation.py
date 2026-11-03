"""Offline tests: Finnhub capture never requires a real credential."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research_capture_finnhub_observation import capture, NoRedirects


class FakeResponse:
    status = 200
    def __init__(self, raw):
        self.raw = raw
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size):
        return self.raw[:size]


class SourceObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "observation.json"
        self.raw = b'{"c":100.25,"t":1793736000}'
        self.opened = []
        def opener(request, timeout):
            self.opened.append(request)
            return FakeResponse(self.raw)
        self.opener = opener
        self.clock = lambda: datetime(2026, 11, 3, 20, tzinfo=timezone.utc)

    def tearDown(self):
        self.temp.cleanup()

    def run_capture(self):
        return capture("AMD", self.path, token="dummy-secret",
                       opener=self.opener, clock=self.clock)

    def test_captures_exact_raw_bytes_without_claiming_prospectivity(self):
        result = self.run_capture()
        record = json.loads(self.path.read_text())
        self.assertEqual(bytes.fromhex(record["raw_response_hex"]), self.raw)
        self.assertEqual(record["source_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertFalse(record["prospective_signal_proven"])
        self.assertFalse(record["trade_ready"])
        self.assertNotIn("dummy-secret", self.path.read_text())
        self.assertNotIn("dummy-secret", str(result))
        self.assertEqual(self.opened[0].get_header("X-finnhub-token"), "dummy-secret")

    def test_does_not_overwrite(self):
        self.run_capture()
        with self.assertRaises(FileExistsError):
            self.run_capture()

    def test_redirect_is_rejected_before_token_can_be_forwarded(self):
        with self.assertRaisesRegex(ValueError, "source_redirect_forbidden"):
            NoRedirects().redirect_request(None, None, 302, "Found", {}, "https://other.example/collect")

    def test_rejects_missing_token_without_network(self):
        with self.assertRaises(ValueError):
            capture("AMD", self.path, token="", opener=self.opener)
        self.assertEqual(self.opened, [])

    def test_rejects_unapproved_symbol(self):
        with self.assertRaises(ValueError):
            capture("OTHER", self.path, token="dummy", opener=self.opener)

    def test_rejects_invalid_quote(self):
        self.raw = b'{"c":0}'
        with self.assertRaisesRegex(ValueError, "source_quote_invalid"):
            self.run_capture()
        self.assertFalse(self.path.exists())

    def test_rejects_provider_response_echoing_credential(self):
        self.raw = b'{"c":100.25,"unexpected":"dummy-secret"}'
        with self.assertRaisesRegex(ValueError, "source_response_contains_credential"):
            self.run_capture()
        self.assertFalse(self.path.exists())

    def test_rejects_oversized_response(self):
        self.raw = b"x" * 65537
        with self.assertRaisesRegex(ValueError, "source_response_size_invalid"):
            self.run_capture()
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
