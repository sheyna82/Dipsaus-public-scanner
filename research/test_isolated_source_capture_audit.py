"""Source capture identity and point-in-time regression tests."""
import hashlib
import unittest
from isolated_source_capture_audit import verify_source_capture

class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = b"offline-source-bytes"
        self.kw = dict(raw_bytes=self.raw, expected_sha256=hashlib.sha256(self.raw).hexdigest(),
            source_available_at="2026-11-05T08:00:00Z",
            captured_at="2026-11-05T09:00:00Z",
            decision_at="2026-11-06T09:00:00Z")

    def test_hash_match_not_authenticity(self):
        result = verify_source_capture(**self.kw)
        self.assertTrue(result["sha256_verified"])
        self.assertFalse(result["source_authenticity_independently_proven"])

    def test_tampered_bytes_block(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_MISMATCH"):
            verify_source_capture(**dict(self.kw, raw_bytes=b"tampered"))

    def test_late_capture_block(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_NOT_AVAILABLE_AT_DECISION"):
            verify_source_capture(**dict(self.kw, captured_at="2026-11-07T09:00:00Z"))

    def test_late_publication_block(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_NOT_AVAILABLE_AT_DECISION"):
            verify_source_capture(**dict(self.kw, source_available_at="2026-11-06T10:00:00Z"))

    def test_naive_timestamp_block(self):
        with self.assertRaisesRegex(ValueError, "NAIVE_SOURCE_TIME"):
            verify_source_capture(**dict(self.kw, decision_at="2026-11-06T09:00:00"))

if __name__ == "__main__":
    unittest.main()
