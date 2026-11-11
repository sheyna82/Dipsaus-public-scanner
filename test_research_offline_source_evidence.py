import hashlib
import socket
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from research_offline_source_evidence import prepare_offline_source_evidence


class OfflineSourceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.when = datetime(2026, 11, 3, 16, tzinfo=timezone.utc)
        self.kw = dict(source_bytes=b'{"price":42}', captured_at_utc=self.when,
                       allowed_hosts={"example.org"})

    def test_offline_bytes_never_access_dns_or_network(self):
        with patch.object(socket, "getaddrinfo", side_effect=AssertionError("DNS used")) as dns:
            with patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
                evidence = prepare_offline_source_evidence("https://example.org/data", **self.kw)
            dns.assert_not_called()
        self.assertEqual(evidence["source_sha256"], hashlib.sha256(self.kw["source_bytes"]).hexdigest())
        self.assertIsNone(evidence["source_http_status"])
        self.assertTrue(evidence["offline_supplied_bytes"])
        self.assertFalse(evidence["independent_source_authentication"])
        self.assertFalse(evidence["independent_timestamp_proof"])
        self.assertFalse(evidence["trade_ready"])

    def test_rejects_unapproved_host(self):
        with self.assertRaisesRegex(ValueError, "source_host_not_allowlisted"):
            prepare_offline_source_evidence("https://other.example/data", **self.kw)

    def test_rejects_non_https_and_local(self):
        for url in ("http://example.org/data", "https://localhost/data",
                    "https://example.org:444/data", "https://example.org/#fragment"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                prepare_offline_source_evidence(url, **self.kw)

    def test_rejects_query_strings_before_archiving(self):
        for url in ("https://example.org/data?apikey=SECRET",
                    "https://example.org/data?symbol=AMD"):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "invalid_https_source_url"):
                prepare_offline_source_evidence(url, **self.kw)

    def test_rejects_invalid_bytes(self):
        for raw in (b"", "not bytes", b"x" * 1_000_001):
            with self.subTest(size=len(raw)), self.assertRaisesRegex(ValueError, "invalid_source_response_size"):
                prepare_offline_source_evidence("https://example.org/data",
                                                **{**self.kw, "source_bytes": raw})

    def test_rejects_naive_timestamp(self):
        with self.assertRaisesRegex(ValueError, "capture_clock_must_be_utc"):
            prepare_offline_source_evidence("https://example.org/data",
                **{**self.kw, "captured_at_utc": datetime(2026, 11, 3)})


if __name__ == "__main__":
    unittest.main()
