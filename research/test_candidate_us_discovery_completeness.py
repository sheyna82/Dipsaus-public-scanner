"""Offline regression tests for read-only discovery completeness audit."""
import unittest
from research.candidate_us_discovery_completeness import audit


class CompletenessTests(unittest.TestCase):
    def test_rejected_symbols_are_visible_as_missing_evidence(self):
        result = audit({"sample_symbols": ["AAA", "BBB", "CCC"],
                        "candidates": [{"symbol": "AAA"}],
                        "failures": {"CCC": "TimeoutError"},
                        "actual_symbols_screened": 2})
        self.assertEqual(result["noncandidate_symbols"], ["BBB"])
        self.assertFalse(result["prospective_validation_ready"])
        self.assertEqual(result["assessment"], "INCOMPLETE_PREOUTCOME_AUDIT")

    def test_invalid_count_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SCREENED_COUNT_MISMATCH"):
            audit({"sample_symbols": ["AAA"], "candidates": [],
                   "failures": {}, "actual_symbols_screened": 0})

    def test_outside_sample_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SYMBOL_OUTSIDE_SAMPLE"):
            audit({"sample_symbols": ["AAA"], "candidates": [{"symbol": "BBB"}],
                   "failures": {}, "actual_symbols_screened": 1})

    def test_duplicate_sample_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_SAMPLE_SYMBOLS"):
            audit({"sample_symbols": ["AAA", "AAA"], "candidates": [],
                   "failures": {}, "actual_symbols_screened": 2})


if __name__ == "__main__":
    unittest.main()
