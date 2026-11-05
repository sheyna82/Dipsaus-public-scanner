"""Synthetic tests for time-ordered swing execution gate."""
import unittest
from research_swing_execution_timestamp_gate import validate_execution_timestamps


def trade():
    return {
        "trade_id": "A",
        "score_available_at": "2026-10-01T18:00:00+00:00",
        "entry_decision_at": "2026-10-01T19:00:00+00:00",
        "entry_execution_at": "2026-10-02T13:30:00+00:00",
        "exit_decision_at": "2026-10-07T20:00:00+00:00",
        "exit_execution_at": "2026-10-08T13:30:00+00:00",
    }


class ExecutionTimestampTests(unittest.TestCase):
    def test_valid_completed_trade(self):
        result = validate_execution_timestamps(
            [trade()], evaluation_cutoff="2026-10-09T00:00:00+00:00")
        self.assertEqual(result["accepted_trade_ids"], ["A"])
        self.assertFalse(result["source_timestamps_independently_attested"])

    def test_score_after_decision_rejected(self):
        x = trade()
        x["score_available_at"] = "2026-10-02T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "lookahead"):
            validate_execution_timestamps([x],
                evaluation_cutoff="2026-10-09T00:00:00+00:00")

    def test_exit_after_cutoff_rejected(self):
        with self.assertRaisesRegex(ValueError, "unmatured"):
            validate_execution_timestamps([trade()],
                evaluation_cutoff="2026-10-08T00:00:00+00:00")

    def test_entry_before_decision_rejected(self):
        x = trade()
        x["entry_execution_at"] = "2026-10-01T18:30:00+00:00"
        with self.assertRaisesRegex(ValueError, "lookahead"):
            validate_execution_timestamps([x],
                evaluation_cutoff="2026-10-09T00:00:00+00:00")

    def test_naive_timestamps_rejected(self):
        x = trade()
        x["score_available_at"] = "2026-10-01T18:00:00"
        with self.assertRaisesRegex(ValueError, "timezone_required"):
            validate_execution_timestamps([x],
                evaluation_cutoff="2026-10-09T00:00:00+00:00")

    def test_duplicate_trade_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_or_invalid"):
            validate_execution_timestamps([trade(), trade()],
                evaluation_cutoff="2026-10-09T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
