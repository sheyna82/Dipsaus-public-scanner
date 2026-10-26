"""Synthetic executable-cost-matched portfolio benchmark tests."""
import unittest
from decimal import Decimal
from research_swing_portfolio_benchmark import compare_portfolio_rankings


def candidates():
    return [
        {"ticker": "A", "eligible": True, "hypothesis_score": 9,
         "baseline_score": 1, "entry_price": 100,
         "daily_closes": [101, 102, 103, 104, 105]},
        {"ticker": "B", "eligible": True, "hypothesis_score": 1,
         "baseline_score": 9, "entry_price": 100,
         "daily_closes": [99, 98, 97, 96, 95]},
    ]


class PortfolioBenchmarkTests(unittest.TestCase):
    def test_equal_capital_one_slot(self):
        result = compare_portfolio_rankings(candidates(), 3500, max_positions=1)
        self.assertEqual(result["hypothesis"]["selected"][0]["ticker"], "A")
        self.assertEqual(result["baseline"]["selected"][0]["ticker"], "B")
        self.assertEqual(Decimal(result["net_pnl_difference"]), 350)

    def test_same_selection_zero_difference(self):
        result = compare_portfolio_rankings(candidates(), 7000, max_positions=2)
        self.assertEqual(Decimal(result["net_pnl_difference"]), 0)

    def test_costs_identical_on_both_sides(self):
        result = compare_portfolio_rankings(
            candidates(), 3500, max_positions=1,
            spread_bps=10, slippage_bps=5, commission_bps=2)
        self.assertEqual(result["hypothesis"]["selected_count"], 1)
        self.assertEqual(result["baseline"]["selected_count"], 1)
        self.assertGreater(Decimal(result["net_pnl_difference"]), 0)

    def test_ineligible_excluded(self):
        x = candidates()
        x[0]["eligible"] = False
        result = compare_portfolio_rankings(x, 3500)
        self.assertEqual(result["hypothesis"]["selected"][0]["ticker"], "B")

    def test_invalid_baseline_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_baseline"):
            compare_portfolio_rankings(candidates(), 3500, baseline_key="future_return")


if __name__ == "__main__":
    unittest.main()
