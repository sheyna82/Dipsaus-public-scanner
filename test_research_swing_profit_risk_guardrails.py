"""Synthetic tests for predeclared swing profit/risk guardrails."""
import unittest
from research_swing_profit_risk_guardrails import assess_profit_risk


def curve(values):
    return [{"date": f"2026-11-{i+2:02d}", "equity": value}
            for i, value in enumerate(values)]


class ProfitRiskGuardrailsTests(unittest.TestCase):
    def test_profitable_low_drawdown_passes(self):
        result = assess_profit_risk({"A": curve([1000, 1020, 1010, 1040])},
                                    min_observations=4)
        self.assertTrue(result["strategies"]["A"]["research_guardrails_met"])
        self.assertFalse(result["best_strategy_selected"])

    def test_profitable_high_drawdown_fails(self):
        result = assess_profit_risk({"A": curve([1000, 2000, 1000, 2100])},
                                    min_observations=4)
        self.assertFalse(result["strategies"]["A"]["drawdown_limit_met"])
        self.assertTrue(result["strategies"]["A"]["positive_net_pnl"])

    def test_insufficient_observations_fails(self):
        result = assess_profit_risk({"A": curve([1000, 1050])})
        self.assertFalse(result["strategies"]["A"]["minimum_sample_met"])

    def test_loss_streak_fails(self):
        result = assess_profit_risk({"A": curve([1000, 990, 980, 970, 1100])},
                                    min_observations=5, max_negative_streak=2)
        self.assertFalse(result["strategies"]["A"]["loss_streak_limit_met"])

    def test_negative_net_pnl_fails(self):
        result = assess_profit_risk({"A": curve([1000, 990, 980])},
                                    min_observations=3)
        self.assertFalse(result["strategies"]["A"]["positive_net_pnl"])

    def test_invalid_limits_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_risk_threshold"):
            assess_profit_risk({"A": curve([1000, 1100])},
                               max_drawdown_pct="NaN")

    def test_multiple_strategies_evaluated_without_winner(self):
        result = assess_profit_risk({
            "A": curve([1000, 1010, 1020]),
            "B": curve([1000, 900, 1200]),
        }, min_observations=3)
        self.assertEqual(set(result["strategies"]), {"A", "B"})
        self.assertFalse(result["best_strategy_selected"])


if __name__ == "__main__":
    unittest.main()
