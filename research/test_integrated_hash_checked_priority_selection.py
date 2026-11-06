"""End-to-end source-hash-backed selection regression tests."""
import hashlib
import unittest
from integrated_hash_checked_priority_selection import compare_hash_checked

RAW_A, RAW_B = b"synthetic source A", b"synthetic source B"
HASH_A, HASH_B = hashlib.sha256(RAW_A).hexdigest(), hashlib.sha256(RAW_B).hexdigest()

def registration(i, priority, digest):
    return {"id": i, "registered_at": "2026-11-05T10:00:00+01:00",
            "source_available_at": "2026-11-05T08:30:00Z",
            "entry_at": "2026-11-06T09:00:00+01:00",
            "source_verified": True, "immutable_registration_verified": True,
            "source_sha256": digest, "registered_priority": priority}

def candidate(i):
    return {"id": i, "entry_date": "2026-11-06", "exit_date": "2026-11-12",
            "allocation_eur": 30000, "research_only": True, "trade_ready": False}

class HashCheckedSelectionTests(unittest.TestCase):
    def test_valid_source_bytes_selects_registered_priority(self):
        result = compare_hash_checked([registration("A", 1, HASH_A), registration("B", 3, HASH_B)],
                                      {HASH_A: RAW_A, HASH_B: RAW_B},
                                      [candidate("A"), candidate("B")])
        self.assertEqual(result["hash_checked_count"], 2)
        self.assertEqual(result["selection"]["priority"]["accepted_ids"], ["B"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["historical_authenticity_independently_proven"])

    def test_tampered_source_blocks_selection(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH_MISMATCH"):
            compare_hash_checked([registration("A", 1, HASH_A)],
                                 {HASH_A: RAW_A + b"changed"}, [candidate("A")])

    def test_missing_source_blocks_selection(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_MISSING"):
            compare_hash_checked([registration("A", 1, HASH_A)], {}, [candidate("A")])

    def test_missing_candidate_registration_blocks(self):
        with self.assertRaisesRegex(ValueError, "CANDIDATE_REGISTRATION_COVERAGE_MISMATCH"):
            compare_hash_checked([registration("A", 1, HASH_A)],
                                 {HASH_A: RAW_A}, [candidate("A"), candidate("B")])

    def test_source_after_registration_blocks(self):
        r = registration("A", 1, HASH_A)
        r["source_available_at"] = "2026-11-05T12:00:00Z"
        with self.assertRaisesRegex(ValueError, "POINT_IN_TIME_VIOLATION"):
            compare_hash_checked([r], {HASH_A: RAW_A}, [candidate("A")])

if __name__ == "__main__":
    unittest.main()
