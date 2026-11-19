"""Synthetic official source snapshot transcript tests."""
import hashlib
import unittest
from research_official_source_snapshot import assess_official_snapshot

URL = "https://www.iso20022.org/market-identifier-codes"
BODY = b"synthetic offline fixture, not an ISO publication"
DIGEST = hashlib.sha256(BODY).hexdigest()

class SnapshotTests(unittest.TestCase):
    def check(self, **kwargs):
        args = {"body": BODY, "source_url": URL, "approved_url": URL,
                "response_status": 200, "expected_sha256": DIGEST}
        args.update(kwargs)
        return assess_official_snapshot(**args)

    def test_valid_metadata_still_not_authenticated(self):
        r = self.check()
        self.assertEqual(r["status"], "OFFLINE_SNAPSHOT_METADATA_CONSISTENT")
        self.assertFalse(r["source_authenticity_independently_verified"])
        self.assertFalse(r["trade_ready"])

    def test_redirect_302_blocked(self):
        self.assertEqual(self.check(response_status=302)["reason"], "HTTP_STATUS_NOT_OK")

    def test_redirect_header_blocked_even_200(self):
        self.assertEqual(self.check(redirect_location="https://example.org")["reason"], "REDIRECT_NOT_APPROVED")

    def test_other_host_blocked(self):
        self.assertEqual(self.check(source_url="https://example.org/file.csv")["reason"], "UNAPPROVED_SOURCE_URL")

    def test_http_blocked(self):
        self.assertEqual(self.check(source_url="http://www.iso20022.org/market-identifier-codes",
                                    approved_url="http://www.iso20022.org/market-identifier-codes")["reason"], "UNSAFE_URL")

    def test_embedded_credentials_blocked(self):
        u = "https://user:pass@www.iso20022.org/market-identifier-codes"
        self.assertEqual(self.check(source_url=u, approved_url=u)["reason"], "UNSAFE_URL")

    def test_fragment_blocked(self):
        u = URL+"#download"
        self.assertEqual(self.check(source_url=u, approved_url=u)["reason"], "UNSAFE_URL")

    def test_digest_mismatch_blocked(self):
        self.assertEqual(self.check(expected_sha256="0"*64)["reason"], "DIGEST_NOT_ATTESTED")

    def test_missing_digest_blocked(self):
        self.assertEqual(self.check(expected_sha256=None)["reason"], "DIGEST_NOT_ATTESTED")

    def test_empty_body_blocked(self):
        self.assertEqual(self.check(body=b"")["reason"], "EMPTY_OR_INVALID_BODY")

    def test_boolean_http_status_blocked(self):
        self.assertEqual(self.check(response_status=True)["reason"], "HTTP_STATUS_NOT_OK")

    def test_modified_body_blocked(self):
        self.assertEqual(self.check(body=BODY+b"tamper")["reason"], "DIGEST_NOT_ATTESTED")

if __name__ == "__main__":
    unittest.main()
