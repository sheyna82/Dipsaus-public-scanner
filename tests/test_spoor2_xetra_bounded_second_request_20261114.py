"""Offline contract tests: no external Xetra requests or trade activation."""
import hashlib
import io
import unittest

from research.spoor2_xetra_bounded_second_request_20261114 import fetch_approved_second_request

CSV = "https://www.cashmarket.deutsche-boerse.com/resource/blob/1528/a4b7965b87cf1ef4621a28b85f145ae9/data/t7-xetr-allTradableInstruments.csv"


class Response:
    def __init__(self, data=b"abc", status=200, url=CSV, length=None):
        self.stream = io.BytesIO(data)
        self.status = status
        self.url = url
        self.headers = {} if length is None else {"Content-Length": length}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, size):
        return self.stream.read(size)


class Opener:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def open(self, request, timeout):
        self.calls += 1
        return self.response


class SecondRequestTests(unittest.TestCase):
    def test_default_deny_does_not_open(self):
        opener = Opener(Response())
        result = fetch_approved_second_request("csv", CSV, opener=opener)
        self.assertEqual(opener.calls, 0)
        self.assertFalse(result["trade_ready"])

    def test_exact_approval_yields_bytes_but_no_attestation(self):
        opener = Opener(Response())
        result = fetch_approved_second_request("csv", CSV, (CSV,), opener)
        self.assertEqual(opener.calls, 1)
        self.assertEqual(result["sha256"], hashlib.sha256(b"abc").hexdigest())
        self.assertEqual(result["byte_count"], 3)
        self.assertFalse(result["source_attested"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["order_placement_enabled"])

    def test_unexpected_final_url_blocks(self):
        result = fetch_approved_second_request(
            "csv", CSV, (CSV,), Opener(Response(url=CSV + "/unexpected"))
        )
        self.assertIsNone(result["bytes"])

    def test_redirect_status_blocks(self):
        result = fetch_approved_second_request(
            "csv", CSV, (CSV,), Opener(Response(status=302))
        )
        self.assertIsNone(result["bytes"])

    def test_invalid_declared_length_blocks(self):
        result = fetch_approved_second_request(
            "csv", CSV, (CSV,), Opener(Response(length="bad"))
        )
        self.assertIsNone(result["bytes"])

    def test_short_body_blocks(self):
        result = fetch_approved_second_request(
            "csv", CSV, (CSV,), Opener(Response(length="4"))
        )
        self.assertIsNone(result["bytes"])

    def test_empty_body_blocks(self):
        result = fetch_approved_second_request(
            "csv", CSV, (CSV,), Opener(Response(data=b""))
        )
        self.assertIsNone(result["bytes"])

    def test_wrong_host_not_requested(self):
        opener = Opener(Response())
        result = fetch_approved_second_request(
            "csv", "https://evil.example/resource/blob/1528/12345678901234567890123456789012/data/t7-xetr-allTradableInstruments.csv",
            (CSV,), opener
        )
        self.assertEqual(opener.calls, 0)
        self.assertFalse(result["trade_ready"])


    def test_declared_size_over_limit_blocks_before_read(self):
        from unittest.mock import patch
        with patch("research.spoor2_xetra_bounded_second_request_20261114.MAX_BYTES", 3):
            result = fetch_approved_second_request(
                "csv", CSV, (CSV,), Opener(Response(data=b"abcd", length="4"))
            )
        self.assertEqual(result["blocks"], ["SECOND_REQUEST_SIZE_LIMIT"])
        self.assertIsNone(result["bytes"])

    def test_streamed_size_over_limit_blocks(self):
        from unittest.mock import patch
        with patch("research.spoor2_xetra_bounded_second_request_20261114.MAX_BYTES", 3):
            result = fetch_approved_second_request(
                "csv", CSV, (CSV,), Opener(Response(data=b"abcd"))
            )
        self.assertEqual(result["blocks"], ["SECOND_REQUEST_SIZE_LIMIT"])
        self.assertIsNone(result["sha256"])

    def test_exact_size_boundary_allowed_but_unattested(self):
        from unittest.mock import patch
        with patch("research.spoor2_xetra_bounded_second_request_20261114.MAX_BYTES", 3):
            result = fetch_approved_second_request(
                "csv", CSV, (CSV,), Opener(Response(data=b"abc", length="3"))
            )
        self.assertEqual(result["byte_count"], 3)
        self.assertFalse(result["source_attested"])
        self.assertFalse(result["trade_ready"])

    def test_http_500_blocks(self):
        result = fetch_approved_second_request(
            "csv", CSV, (CSV,), Opener(Response(status=500))
        )
        self.assertEqual(result["blocks"], ["SECOND_REQUEST_URL_OR_STATUS_MISMATCH"])
        self.assertIsNone(result["bytes"])

    def test_http_error_exception_blocks(self):
        import urllib.error

        class ErrorOpener:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(CSV, 503, "Unavailable", {}, None)

        result = fetch_approved_second_request("csv", CSV, (CSV,), ErrorOpener())
        self.assertEqual(result["blocks"], ["SECOND_REQUEST_HTTP_ERROR"])
        self.assertEqual(result["http_status"], 503)
        self.assertFalse(result["order_placement_enabled"])

    def test_network_error_blocks(self):
        import urllib.error

        class ErrorOpener:
            def open(self, request, timeout):
                raise urllib.error.URLError("offline")

        result = fetch_approved_second_request("csv", CSV, (CSV,), ErrorOpener())
        self.assertEqual(result["blocks"], ["SECOND_REQUEST_TRANSPORT_ERROR"])
        self.assertIsNone(result["bytes"])

    def test_unknown_kind_never_opens(self):
        opener = Opener(Response())
        result = fetch_approved_second_request("unknown", CSV, (CSV,), opener)
        self.assertEqual(opener.calls, 0)
        self.assertFalse(result["trade_ready"])

    def test_non_exact_approval_never_opens(self):
        opener = Opener(Response())
        result = fetch_approved_second_request("csv", CSV, (CSV + "/",), opener)
        self.assertEqual(opener.calls, 0)
        self.assertFalse(result["source_attested"])


if __name__ == "__main__":
    unittest.main()
