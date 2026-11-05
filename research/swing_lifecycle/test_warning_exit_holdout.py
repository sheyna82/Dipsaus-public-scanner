import unittest
from datetime import date, timedelta
from research.swing_lifecycle.test_warning_portfolio_comparison import case
from research.swing_lifecycle.warning_exit_holdout import evaluate_warning_exit_holdout


def shifted(ticker, days):
    item = case(ticker=ticker, warning=True)
    for bar in item["bars"]:
        bar["date"] = (date.fromisoformat(bar["date"]) +
                       timedelta(days=days)).isoformat()
    return item


class WarningExitHoldoutTests(unittest.TestCase):
    def test_purged_chronological_split(self):
        old = shifted("OLD", 0)
        near = shifted("NEAR", 25)
        future = shifted("NEW", 80)
        result = evaluate_warning_exit_holdout(
            [old, near, future], cutoff=date(2026, 2, 15),
            embargo_days=15)
        self.assertEqual(result["training"]["trade_candidates"], 1)
        self.assertEqual(result["holdout"]["trade_candidates"], 1)
        self.assertEqual(result["purged_crossing_or_near_cutoff"], 1)
        self.assertFalse(result["historical_edge_proven"])

    def test_empty_holdout_is_not_misreported_as_zero_edge(self):
        result = evaluate_warning_exit_holdout(
            [shifted("OLD", 0)], cutoff=date(2026, 2, 15))
        self.assertEqual(result["holdout"]["trade_candidates"], 0)
        self.assertIsNone(result["holdout"]["result"])

    def test_invalid_split_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_split"):
            evaluate_warning_exit_holdout([], cutoff="2026-02-15")


if __name__ == "__main__":
    unittest.main()
