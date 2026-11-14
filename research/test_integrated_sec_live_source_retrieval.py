"""Offline SEC source retrieval tests: no external network calls."""
import hashlib
import io
import unittest
from unittest.mock import patch
from integrated_sec_live_source_retrieval import retrieve_sec_complete_submission

URL = ("https://www.sec.gov/Archives/edgar/data/123456/"
       "000012345626000001/0000123456-26-000001.txt")
AGENT = "Dipsaus Research research@example.org"


class FakeResponse:
    status = 200

    def __init__(self, data):
        self.stream = io.BytesIO(data)

    def geturl(self):
        return URL

    def read(self, n):
        return self.stream.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class SecSourceRetrievalTests(unittest.TestCase):
    def test_bounded_bytes_and_receipt_do_not_claim_history(self):
        data = b"<SEC-HEADER>\n<ACCEPTANCE-DATETIME>20261105163000\n"
        class FakeOpener:
            def open(self, request, timeout):
                self.assert_placeholder = timeout
                return FakeResponse(data)
        with patch("urllib.request.build_opener", return_value=FakeOpener()):
            raw, receipt = retrieve_sec_complete_submission(URL, AGENT)
        self.assertEqual(raw, data)
        self.assertEqual(receipt["sha256"], hashlib.sha256(data).hexdigest())
        self.assertFalse(receipt["historical_publication_independently_proven"])
        self.assertFalse(receipt["eligible_for_performance_claim"])

    def test_oversized_document_fails_closed(self):
        class FakeOpener:
            def open(self, request, timeout):
                return FakeResponse(b"x" * 9)
        with patch("urllib.request.build_opener", return_value=FakeOpener()):
            with self.assertRaisesRegex(ValueError, "SEC_SOURCE_EMPTY_OR_OVERSIZED"):
                retrieve_sec_complete_submission(URL, AGENT, max_bytes=8)

    def test_untrusted_url_and_missing_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_SEC_SOURCE_URL"):
            retrieve_sec_complete_submission(URL.replace("www.sec.gov", "evil.example"), AGENT)
        for malformed in (
            URL.replace("/0000123456-26-000001.txt", "/other.txt"),
            URL.replace("/000012345626000001/", "/../../"),
            URL.replace("/Archives/edgar/data/", "/Archives/edgar/data/123456/"),
            URL + "#fragment",
        ):
            with self.subTest(url=malformed):
                with self.assertRaisesRegex(ValueError, "INVALID_SEC_SOURCE_URL"):
                    retrieve_sec_complete_submission(malformed, AGENT)
        with self.assertRaisesRegex(ValueError, "SEC_IDENTIFYING_USER_AGENT_REQUIRED"):
            retrieve_sec_complete_submission(URL, "bot")


if __name__ == "__main__":
    unittest.main()
