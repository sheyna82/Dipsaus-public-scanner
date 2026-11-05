"""Synthetic tests for sampled equity risk accounting."""
import unittest
from decimal import Decimal
from research_swing_equity_risk import summarize_equity_curve


def observations(values):
    return [{"date": f"2026-11-{i+2:02d}", "equity": v}
            for i, v in enumerate(values)]


class EquityRiskTests(unittest.TestCase):
    def test_drawdown_and_recovery(self):
        result = summarize_equity_curve(observations([1000, 1100, 990, 1050, 1200]))
        self.assertEqual(Decimal(result["max_observed_drawdown_pct"]), 10)
        self.assertEqual(result["longest_underwater_observations"], 2)
        self.assertEqual(result["longest_negative_streak"], 1)
        self.assertEqual(Decimal(result["net_pnl"]), 200)

    def test_two_consecutive_losses(self):
        result = summarize_equity_curve(observations([1000, 950, 900, 920]))
        self.assertEqual(result["longest_negative_streak"], 2)
        self.assertEqual(result["negative_period_count"], 2)

    def test_flat_portfolio(self):
        result = summarize_equity_curve(observations([1000, 1000, 1000]))
        self.assertEqual(Decimal(result["max_observed_drawdown_pct"]), 0)
        self.assertEqual(result["longest_underwater_observations"], 0)

    def test_unsorted_dates_rejected(self):
        x = observations([1000, 900])
        x.reverse()
        with self.assertRaisesRegex(ValueError, "equity_not_chronological"):
            summarize_equity_curve(x)

    def test_duplicate_date_rejected(self):
        x = observations([1000, 900])
        x[1]["date"] = x[0]["date"]
        with self.assertRaisesRegex(ValueError, "duplicate_equity_date"):
            summarize_equity_curve(x)

    def test_negative_equity_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_equity"):
            summarize_equity_curve(observations([1000, -1]))

    def test_insufficient_observations_rejected(self):
        with self.assertRaisesRegex(ValueError, "insufficient_equity"):
            summarize_equity_curve(observations([1000]))


if __name__ == "__main__":
    unittest.main()
