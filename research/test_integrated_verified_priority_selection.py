"""Regression tests for registration-backed portfolio selection."""
import unittest
from integrated_verified_priority_selection import compare_verified

def registration(ident, priority):
    return {"id": ident, "registered_at": "2026-11-05T10:00:00+01:00",
            "source_available_at": "2026-11-05T08:30:00Z",
            "entry_at": "2026-11-06T09:00:00+01:00",
            "source_verified": True, "immutable_registration_verified": True,
            "source_sha256": "a" * 64, "registered_priority": priority}

def candidate(ident):
    return {"id": ident, "entry_date": "2026-11-06", "exit_date": "2026-11-12",
            "allocation_eur": 30000, "research_only": True, "trade_ready": False}

class VerifiedSelectionTests(unittest.TestCase):
    def test_registered_priority_changes_choice(self):
        result = compare_verified([registration("A", 1), registration("B", 3)],
                                  [candidate("A"), candidate("B")])
        self.assertEqual(result["selection"]["baseline"]["accepted_ids"], ["A"])
        self.assertEqual(result["selection"]["priority"]["accepted_ids"], ["B"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["historical_authenticity_independently_proven"])

    def test_missing_registration_blocks(self):
        with self.assertRaisesRegex(ValueError, "CANDIDATE_REGISTRATION_COVERAGE_MISMATCH"):
            compare_verified([registration("A", 1)], [candidate("A"), candidate("B")])

    def test_extra_registration_blocks(self):
        with self.assertRaisesRegex(ValueError, "CANDIDATE_REGISTRATION_COVERAGE_MISMATCH"):
            compare_verified([registration("A", 1), registration("B", 2)], [candidate("A")])

    def test_candidate_priority_override_blocks(self):
        item = candidate("A")
        item["registered_priority"] = 100
        with self.assertRaisesRegex(ValueError, "CANDIDATE_EVIDENCE_OVERRIDE_BLOCKED"):
            compare_verified([registration("A", 1)], [item])

    def test_registration_after_entry_blocks(self):
        r = registration("A", 1)
        r["registered_at"] = "2026-11-06T10:00:00+01:00"
        with self.assertRaisesRegex(ValueError, "POINT_IN_TIME_VIOLATION"):
            compare_verified([r], [candidate("A")])

    def test_candidate_id_mismatch_blocks(self):
        with self.assertRaisesRegex(ValueError, "UNREGISTERED_CANDIDATE"):
            compare_verified([registration("A", 1)], [candidate("B")])

    def test_duplicate_candidate_blocks(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CANDIDATE"):
            compare_verified([registration("A", 1), registration("B", 2)],
                             [candidate("A"), candidate("A")])

if __name__ == "__main__":
    unittest.main()
