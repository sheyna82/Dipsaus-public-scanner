"""Independent source bytes hash regression tests."""
import hashlib
import unittest
from integrated_historical_source_bytes_gate import verify_sources

RAW = b"synthetic historical research source"
DIGEST = hashlib.sha256(RAW).hexdigest()

def registration():
    return {"id": "A", "registered_at": "2026-11-05T10:00:00+01:00",
            "source_available_at": "2026-11-05T08:30:00Z",
            "entry_at": "2026-11-06T09:00:00+01:00",
            "source_verified": True, "immutable_registration_verified": True,
            "source_sha256": DIGEST, "registered_priority": 2}

class SourceBytesTests(unittest.TestCase):
    def test_valid_source_bytes(self):
        result = verify_sources([registration()], {DIGEST: RAW})
        self.assertTrue(result["source_bytes_verified"][0]["bytes_hash_verified"])
        self.assertFalse(result["external_publication_time_independently_proven"])
        self.assertFalse(result["trade_ready"])

    def test_tampered_bytes_blocked(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH_MISMATCH"):
            verify_sources([registration()], {DIGEST: RAW + b"tampered"})

    def test_missing_bytes_blocked(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_MISSING"):
            verify_sources([registration()], {})

    def test_non_bytes_blocked(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_MISSING"):
            verify_sources([registration()], {DIGEST: "text"})

    def test_unverified_registration_blocked(self):
        r = registration()
        r["source_verified"] = False
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_PROVENANCE"):
            verify_sources([r], {DIGEST: RAW})

    def test_invalid_timestamp_blocks(self):
        r = registration()
        r["registered_at"] = "2026-11-07T10:00:00+01:00"
        with self.assertRaisesRegex(ValueError, "POINT_IN_TIME_VIOLATION"):
            verify_sources([r], {DIGEST: RAW})

    def test_empty_source_set(self):
        result = verify_sources([], {})
        self.assertEqual(result["source_bytes_verified"], [])

if __name__ == "__main__":
    unittest.main()
