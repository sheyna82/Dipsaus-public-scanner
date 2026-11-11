"""Ensure no evaluation occurs before every timestamp is checked."""
import unittest
from research_swing_timestamp_gated_pipeline import evaluate_timestamp_gated_batch


def trade(id_="A"):
    return {"trade_id": id_,
            "score_available_at": "2026-10-01T18:00:00+00:00",
            "entry_decision_at": "2026-10-01T19:00:00+00:00",
            "entry_execution_at": "2026-10-02T13:30:00+00:00",
            "exit_decision_at": "2026-10-07T20:00:00+00:00",
            "exit_execution_at": "2026-10-08T13:30:00+00:00"}


class GatedPipelineTests(unittest.TestCase):
    def test_valid_batch_evaluated_once(self):
        calls = []
        result = evaluate_timestamp_gated_batch(
            [trade()], evaluation_cutoff="2026-10-09T00:00:00+00:00",
            evaluator=lambda x: calls.append(len(x)) or {"pnl": "10"})
        self.assertEqual(calls, [1])
        self.assertTrue(result["timestamp_gate_passed"])

    def test_invalid_batch_never_evaluated(self):
        calls = []
        bad = trade("B")
        bad["score_available_at"] = "2026-10-03T18:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "lookahead"):
            evaluate_timestamp_gated_batch(
                [trade(), bad], evaluation_cutoff="2026-10-09T00:00:00+00:00",
                evaluator=lambda x: calls.append(x))
        self.assertEqual(calls, [])

    def test_unmatured_outcome_never_evaluated(self):
        calls = []
        with self.assertRaisesRegex(ValueError, "unmatured"):
            evaluate_timestamp_gated_batch(
                [trade()], evaluation_cutoff="2026-10-08T00:00:00+00:00",
                evaluator=lambda x: calls.append(x))
        self.assertEqual(calls, [])

    def test_duplicate_trade_never_evaluated(self):
        with self.assertRaisesRegex(ValueError, "duplicate_or_invalid"):
            evaluate_timestamp_gated_batch(
                [trade(), trade()], evaluation_cutoff="2026-10-09T00:00:00+00:00",
                evaluator=lambda x: self.fail("evaluator should not run"))

    def test_invalid_evaluator_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_evaluator"):
            evaluate_timestamp_gated_batch(
                [trade()], evaluation_cutoff="2026-10-09T00:00:00+00:00",
                evaluator=None)


if __name__ == "__main__":
    unittest.main()
