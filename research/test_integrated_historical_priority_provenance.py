"""Point-in-time historical priority evidence tests."""
import unittest
from integrated_historical_priority_provenance import validate

def record():
    return {"id": "ASML-001", "registered_at": "2026-11-05T10:00:00+01:00",
            "source_available_at": "2026-11-05T08:30:00Z",
            "entry_at": "2026-11-06T09:00:00+01:00",
            "source_verified": True, "immutable_registration_verified": True,
            "source_sha256": "a" * 64, "registered_priority": "2.5"}

class ProvenanceTests(unittest.TestCase):
    def test_valid_timestamp_order(self):
        result = validate([record()])
        self.assertEqual(result["verified_registrations"][0]["registered_priority"], 2.5)
        self.assertFalse(result["historical_authenticity_independently_proven"])

    def test_future_source_blocks(self):
        r = record()
        r["source_available_at"] = "2026-11-05T12:00:00Z"
        with self.assertRaisesRegex(ValueError, "POINT_IN_TIME_VIOLATION"):
            validate([r])

    def test_registration_after_entry_blocks(self):
        r = record()
        r["entry_at"] = "2026-11-05T09:00:00+01:00"
        with self.assertRaisesRegex(ValueError, "POINT_IN_TIME_VIOLATION"):
            validate([r])

    def test_naive_timestamp_blocks(self):
        r = record()
        r["registered_at"] = "2026-11-05T10:00:00"
        with self.assertRaisesRegex(ValueError, "NAIVE_TIMESTAMP"):
            validate([r])

    def test_unverified_source_blocks(self):
        r = record()
        r["source_verified"] = False
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_PROVENANCE"):
            validate([r])

    def test_invalid_sha_blocks(self):
        r = record()
        r["source_sha256"] = "fake"
        with self.assertRaisesRegex(ValueError, "INVALID_SOURCE_SHA256"):
            validate([r])

    def test_future_outcome_blocks(self):
        r = record()
        r["future_return"] = 0.1
        with self.assertRaisesRegex(ValueError, "OUTCOME_LEAKAGE"):
            validate([r])

    def test_duplicate_registration_blocks(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_REGISTRATION"):
            validate([record(), record()])

    def test_nonfinite_priority_blocks(self):
        r = record()
        r["registered_priority"] = "NaN"
        with self.assertRaisesRegex(ValueError, "INVALID_PRIORITY"):
            validate([r])

if __name__ == "__main__":
    unittest.main()
