"""Source identity metadata never attests the source by itself."""
import unittest
from research.us_source_identity_20261117 import review_source_identity


class SourceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "provider_id": "synthetic-A", "dataset_id": "synthetic-bars-001",
            "instrument_id": "US-SYNTH", "mic": "XNAS",
            "retrieval_url": "https://example.org/data/bars",
            "retrieval_reference": "offline-fixture",
            "license_reference": "offline-fixture",
            "content_sha256": "a" * 64,
        }

    def test_complete_metadata_is_still_unverified(self):
        result = review_source_identity(self.record)
        self.assertEqual(result["status"], "METADATA_COMPLETE_UNVERIFIED")
        self.assertFalse(result["provider_independently_verified"])
        self.assertFalse(result["license_verified"])
        self.assertFalse(result["mic_verified"])
        self.assertFalse(result["trade_ready"])

    def test_missing_provider_blocks(self):
        record = dict(self.record, provider_id="")
        self.assertIn("MISSING_PROVIDER_ID", review_source_identity(record)["blocks"])

    def test_bad_mic_format_blocks(self):
        record = dict(self.record, mic="NASDAQ")
        self.assertIn("INVALID_MIC_FORMAT", review_source_identity(record)["blocks"])

    def test_non_https_url_blocks(self):
        record = dict(self.record, retrieval_url="http://example.org/data")
        self.assertIn("RETRIEVAL_URL_NOT_ACCEPTED", review_source_identity(record)["blocks"])

    def test_embedded_credentials_block(self):
        record = dict(self.record, retrieval_url="https://user:pass@example.org/data")
        self.assertIn("RETRIEVAL_URL_NOT_ACCEPTED", review_source_identity(record)["blocks"])

    def test_empty_username_blocks(self):
        record = dict(self.record, retrieval_url="https://@example.org/data")
        self.assertIn("RETRIEVAL_URL_NOT_ACCEPTED", review_source_identity(record)["blocks"])

    def test_whitespace_in_url_blocks(self):
        record = dict(self.record, retrieval_url="https://example.org/a b")
        self.assertIn("RETRIEVAL_URL_NOT_ACCEPTED", review_source_identity(record)["blocks"])

    def test_bad_digest_format_blocks(self):
        record = dict(self.record, content_sha256="a" * 63)
        self.assertIn("INVALID_SHA256_FORMAT", review_source_identity(record)["blocks"])


if __name__ == "__main__":
    unittest.main()
