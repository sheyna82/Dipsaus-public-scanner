import hashlib
import io
import socket
import ssl
import unittest
import urllib.error

from research.spoor2_xetra_artifact_retrieval_20261113 import MAX_BYTES, SOURCES, public_metadata, retrieve_xetra_artifact


class Response:
    status = 200

    def __init__(self, payload, url, declared=None):
        self.payload = io.BytesIO(payload)
        self.url = url
        self.headers = {} if declared is None else {"Content-Length": declared}

    def geturl(self):
        return self.url

    def read(self, size):
        return self.payload.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Opener:
    def __init__(self, response):
        self.response = response

    def open(self, request, timeout):
        return self.response


class XetraArtifactRetrievalTests(unittest.TestCase):
    def test_unknown_kind_fails_closed(self):
        self.assertIn("UNKNOWN_XETRA_ARTIFACT", retrieve_xetra_artifact("other")["blocks"])

    def test_success_is_still_not_attested(self):
        payload = b"ISIN\nDE0006231004\n"
        r = retrieve_xetra_artifact("csv", Opener(Response(payload, SOURCES["csv"])))
        self.assertEqual(r["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(r["byte_count"], len(payload))
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])
        self.assertNotIn("bytes", public_metadata(r))

    def test_redirected_url_rejected(self):
        r = retrieve_xetra_artifact("zip", Opener(Response(b"x", "https://other.example/")))
        self.assertIn("XETRA_URL_OR_HTTP_STATUS_MISMATCH", r["blocks"])

    def test_declared_oversize_rejected(self):
        r = retrieve_xetra_artifact("csv", Opener(Response(b"x", SOURCES["csv"], str(MAX_BYTES + 1))))
        self.assertIn("XETRA_SIZE_LIMIT", r["blocks"])

    def test_stream_oversize_rejected(self):
        r = retrieve_xetra_artifact("csv", Opener(Response(b"x" * (MAX_BYTES + 1), SOURCES["csv"])))
        self.assertIn("XETRA_SIZE_LIMIT", r["blocks"])

    def test_empty_rejected(self):
        r = retrieve_xetra_artifact("zip", Opener(Response(b"", SOURCES["zip"])))
        self.assertIn("EMPTY_XETRA_ARTIFACT", r["blocks"])

    def test_network_error_rejected(self):
        class Broken:
            def open(self, request, timeout):
                raise urllib.error.URLError("offline")
        r = retrieve_xetra_artifact("zip", Broken())
        self.assertIn("XETRA_DOWNLOAD_FAILED", r["blocks"])


    def test_http_error_classified_without_error_body(self):
        class Broken:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(SOURCES["csv"], 403, "secret", {}, None)
        out = retrieve_xetra_artifact("csv", Broken())
        self.assertEqual(out["failure_category"], "HTTP_ERROR")
        self.assertEqual(out["http_status"], 403)
        self.assertNotIn("secret", str(public_metadata(out)))

    def test_dns_error_classified(self):
        class Broken:
            def open(self, request, timeout):
                raise urllib.error.URLError(socket.gaierror(-2, "private hostname"))
        out = retrieve_xetra_artifact("csv", Broken())
        self.assertEqual(out["failure_category"], "DNS_ERROR")
        self.assertNotIn("private hostname", str(public_metadata(out)))

    def test_timeout_classified(self):
        class Broken:
            def open(self, request, timeout):
                raise TimeoutError("private address")
        out = retrieve_xetra_artifact("csv", Broken())
        self.assertEqual(out["failure_category"], "TIMEOUT")

    def test_tls_error_classified(self):
        class Broken:
            def open(self, request, timeout):
                raise urllib.error.URLError(ssl.SSLError("private certificate"))
        out = retrieve_xetra_artifact("csv", Broken())
        self.assertEqual(out["failure_category"], "TLS_ERROR")
        self.assertFalse(out["source_attested"])


    def test_same_host_https_redirect_only_diagnosed(self):
        class Broken:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(SOURCES["csv"], 302, "redirect",
                                             {"Location": "https://www.cashmarket.deutsche-boerse.com/new/private?token=secret"}, None)
        out = retrieve_xetra_artifact("csv", Broken())
        self.assertEqual(out["redirect_diagnostic"], {
            "location_present": True, "absolute_https": True,
            "same_hostname": True,
            "location_sha256": hashlib.sha256(
                b"https://www.cashmarket.deutsche-boerse.com/new/private?token=secret"
            ).hexdigest(),
            "has_query": True, "has_fragment": False,
            "target_not_followed": True})
        self.assertNotIn("secret", str(public_metadata(out)))
        self.assertIsNone(out["bytes"])

    def test_malformed_redirect_header_fails_closed(self):
        class Broken:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(SOURCES["csv"], 302, "redirect",
                                             {"Location": "https://[malformed"}, None)
        out = retrieve_xetra_artifact("csv", Broken())
        self.assertEqual(out["http_status"], 302)
        self.assertTrue(out["redirect_diagnostic"]["malformed_location"])
        self.assertTrue(out["redirect_diagnostic"]["target_not_followed"])
        self.assertFalse(out["source_attested"])
        self.assertFalse(out["trade_ready"])
        self.assertFalse(out["order_placement_enabled"])

    def test_external_redirect_not_followed(self):
        class Broken:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(SOURCES["csv"], 302, "redirect",
                                             {"Location": "https://untrusted.example/secret"}, None)
        out = retrieve_xetra_artifact("csv", Broken())
        self.assertFalse(out["redirect_diagnostic"]["same_hostname"])
        self.assertFalse(out["trade_ready"])

    def test_relative_redirect_not_assumed_safe(self):
        class Broken:
            def open(self, request, timeout):
                raise urllib.error.HTTPError(SOURCES["csv"], 302, "redirect",
                                             {"Location": "/different-path"}, None)
        out = retrieve_xetra_artifact("csv", Broken())
        self.assertFalse(out["redirect_diagnostic"]["absolute_https"])
        self.assertTrue(out["redirect_diagnostic"]["target_not_followed"])


if __name__ == "__main__":
    unittest.main()
