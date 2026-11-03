import hashlib
import io
import socket
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from research_public_https_source_capture import capture_public_https_source, RejectRedirects


class FakeResponse:
    status = 200
    def __init__(self, url, raw):
        self.url, self.buffer = url, io.BytesIO(raw)
    def geturl(self):
        return self.url
    def read(self, n):
        return self.buffer.read(n)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, url, raw):
        self.url, self.raw = url, raw
    def open(self, request, timeout):
        return FakeResponse(self.url, self.raw)


class PublicHttpsCaptureTests(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.org/market.json"
        self.clock = lambda: datetime(2026, 11, 3, 16, tzinfo=timezone.utc)
        self.dns = patch("research_public_https_source_capture.socket.getaddrinfo",
                         return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 443))])
        self.dns.start()

    def tearDown(self):
        self.dns.stop()

    def capture(self, url=None, raw=b'{"fixture":true}'):
        return capture_public_https_source(url or self.url, clock=self.clock,
                allowed_hosts={"example.org"}, opener=FakeOpener(url or self.url, raw))

    def test_captures_bytes_with_unverified_provenance(self):
        result = self.capture()
        self.assertEqual(result["source_sha256"], hashlib.sha256(b'{"fixture":true}').hexdigest())
        self.assertEqual(result["source_captured_at_utc"], "2026-11-03T16:00:00Z")
        self.assertFalse(result["independent_timestamp_proof"])
        self.assertFalse(result["trade_ready"])

    def test_rejects_unapproved_host(self):
        with self.assertRaisesRegex(ValueError, "source_host_not_allowlisted"):
            self.capture("https://other.example/market.json")

    def test_rejects_private_dns(self):
        with patch("research_public_https_source_capture.socket.getaddrinfo",
                   return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaisesRegex(ValueError, "nonpublic_source_address"):
                self.capture()

    def test_rejects_oversized_body(self):
        with self.assertRaisesRegex(ValueError, "invalid_source_response_size"):
            self.capture(raw=b"x" * 1_000_001)

    def test_rejects_redirect_target(self):
        with self.assertRaisesRegex(ValueError, "redirects_not_supported"):
            capture_public_https_source(self.url, clock=self.clock,
                allowed_hosts={"example.org"}, opener=FakeOpener("https://example.org/elsewhere", b"x"))

    def test_redirect_handler_rejects_before_following(self):
        with self.assertRaisesRegex(ValueError, "redirects_not_supported"):
            RejectRedirects().redirect_request(None, None, 302, "redirect", {}, "https://localhost/private")


if __name__ == "__main__":
    unittest.main()
