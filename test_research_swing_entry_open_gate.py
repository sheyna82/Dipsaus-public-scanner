"""Synthetic tests for next-open entry evidence gate."""
import unittest
from research_swing_entry_open_gate import validate_next_open_entries


def candidate():
    return {"ticker": "A", "entry_price": 101,
            "entry_open_price": 101,
            "score_available_at": "2026-10-01T18:00:00+00:00",
            "entry_decision_at": "2026-10-01T19:00:00+00:00",
            "entry_execution_at": "2026-10-02T13:30:00+00:00",
            "entry_open_timestamp": "2026-10-02T13:30:00+00:00"}


class EntryOpenGateTests(unittest.TestCase):
    def test_valid_next_open(self):
        result = validate_next_open_entries([candidate()])
        self.assertTrue(result["next_open_entry_validated"])
        self.assertFalse(result["source_authenticity_verified"])

    def test_mismatched_open_price_rejected(self):
        x = candidate()
        x["entry_open_price"] = 102
        with self.assertRaisesRegex(ValueError, "entry_price_not_next_open"):
            validate_next_open_entries([x])

    def test_open_before_decision_rejected(self):
        x = candidate()
        x["entry_open_timestamp"] = "2026-10-01T13:30:00+00:00"
        with self.assertRaisesRegex(ValueError, "entry_lookahead"):
            validate_next_open_entries([x])

    def test_missing_open_timestamp_rejected(self):
        x = candidate()
        del x["entry_open_timestamp"]
        with self.assertRaisesRegex(ValueError, "invalid_market_timestamp"):
            validate_next_open_entries([x])

    def test_duplicate_ticker_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_or_invalid"):
            validate_next_open_entries([candidate(), candidate()])

    def test_nonfinite_price_rejected(self):
        x = candidate()
        x["entry_open_price"] = "NaN"
        with self.assertRaisesRegex(ValueError, "invalid_entry_open"):
            validate_next_open_entries([x])


if __name__ == "__main__":
    unittest.main()
