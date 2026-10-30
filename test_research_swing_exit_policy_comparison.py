"""Synthetic regression tests for next-open exit-policy comparisons."""
import unittest
from decimal import Decimal
from research_swing_exit_policy_comparison import compare_exit_policies


def trades():
    return [{"ticker": "A", "entry_price": 100, "capital": 3500,
             "daily_closes": [102, 106, 105, 103, 101],
             "next_opens": [101, 98, 104, 102, 100]},
            {"ticker": "B", "entry_price": 100, "capital": 3500,
             "daily_closes": [99, 98, 97, 96, 95],
             "next_opens": [99, 98, 97, 96, 95]}]


class ExitPolicyTests(unittest.TestCase):
    def test_three_policies_returned(self):
        result = compare_exit_policies(trades())
        self.assertEqual(set(result["results"]), {
            "fixed_horizon", "close_target_next_open",
            "close_trailing_next_open"})
        self.assertFalse(result["policy_selection_from_this_sample_allowed"])

    def test_target_gap_can_reduce_profit(self):
        result = compare_exit_policies(trades(), target_pct=5)
        target = result["results"]["close_target_next_open"]["trades"][0]
        self.assertEqual(target["exit_decision_session"], 2)
        self.assertEqual(Decimal(target["net_pnl"]), Decimal("-70.00"))

    def test_fixed_horizon_exit_day(self):
        result = compare_exit_policies(trades(), horizon=3)
        self.assertEqual(result["results"]["fixed_horizon"]["trades"][0]
                         ["exit_decision_session"], 3)

    def test_duplicate_ticker_rejected(self):
        x = trades()
        x[1]["ticker"] = "A"
        with self.assertRaisesRegex(ValueError, "duplicate_ticker"):
            compare_exit_policies(x)

    def test_costs_affect_all_policies(self):
        base = compare_exit_policies(trades())
        costly = compare_exit_policies(trades(), spread_bps=10,
                                       slippage_bps=5, commission_bps=2)
        for name in base["results"]:
            self.assertLess(Decimal(costly["results"][name]["net_pnl"]),
                            Decimal(base["results"][name]["net_pnl"]))

    def test_incomplete_next_open_rejected(self):
        x = trades()
        x[0]["next_opens"] = [101]
        with self.assertRaisesRegex(ValueError, "incomplete_next_open"):
            compare_exit_policies(x)


if __name__ == "__main__":
    unittest.main()
