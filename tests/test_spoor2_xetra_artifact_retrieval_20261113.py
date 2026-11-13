import hashlib
import io
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


if __name__ == "__main__":
    unittest.main()
