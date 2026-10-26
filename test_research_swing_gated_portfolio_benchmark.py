"""Synthetic end-to-end tests: timestamp gate -> portfolio benchmark."""
import unittest
from decimal import Decimal
from research_swing_gated_portfolio_benchmark import evaluate_gated_portfolio_benchmark


def cohort():
    base = {
        "eligible": True, "entry_price": 100,
        "daily_closes": [101, 102, 103, 104, 105],
        "next_opens": [101, 102, 103, 104, 105],
        "score_available_at": "2026-10-01T18:00:00+00:00",
        "entry_decision_at": "2026-10-01T19:00:00+00:00",
        "entry_execution_at": "2026-10-02T13:30:00+00:00",
        "exit_decision_at": "2026-10-07T20:00:00+00:00",
        "exit_execution_at": "2026-10-08T13:30:00+00:00",
    }
    return [
        {**base, "trade_id": "A", "ticker": "A", "hypothesis_score": 9,
         "baseline_score": 1},
        {**base, "trade_id": "B", "ticker": "B", "hypothesis_score": 1,
         "baseline_score": 9, "daily_closes": [99, 98, 97, 96, 95],
         "next_opens": [99, 98, 97, 96, 95]},
    ]


class GatedPortfolioBenchmarkTests(unittest.TestCase):
    def test_realistic_portfolio_benchmark_after_gate(self):
        result = evaluate_gated_portfolio_benchmark(
            cohort(), 3500, max_positions=1, horizon=3,
            evaluation_cutoff="2026-10-09T00:00:00+00:00")
        self.assertTrue(result["timestamp_gate_passed"])
        self.assertEqual(result["analysis"]["execution_model"], "next_session_open")
        self.assertGreater(Decimal(result["analysis"]["net_pnl_difference"]), 0)

    def test_future_score_rejected(self):
        x = cohort()
        x[1]["score_available_at"] = "2026-10-02T18:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "lookahead"):
            evaluate_gated_portfolio_benchmark(
                x, 3500, evaluation_cutoff="2026-10-09T00:00:00+00:00")

    def test_unmatured_outcome_rejected(self):
        with self.assertRaisesRegex(ValueError, "unmatured"):
            evaluate_gated_portfolio_benchmark(
                cohort(), 3500, evaluation_cutoff="2026-10-07T00:00:00+00:00")

    def test_optimistic_legacy_execution_rejected(self):
        with self.assertRaisesRegex(ValueError, "next_open_execution_required"):
            evaluate_gated_portfolio_benchmark(
                cohort(), 3500, evaluation_cutoff="2026-10-09T00:00:00+00:00",
                execution_model="close_optimistic_legacy")

    def test_ineligible_cohort_rejected(self):
        x = cohort()
        x[1]["eligible"] = False
        with self.assertRaisesRegex(ValueError, "ineligible_candidate"):
            evaluate_gated_portfolio_benchmark(
                x, 3500, evaluation_cutoff="2026-10-09T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
