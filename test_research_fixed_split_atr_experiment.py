"""Synthetic regression checks for fixed-schedule folds."""
import unittest
from datetime import date, timedelta
from research_fixed_split_atr_experiment import evaluate_fixed_splits


def prices():
    lines = ["date,open,high,low,close,volume"]
    for i in range(150):
        c = 100 + i * .1
        lines.append(f"{date(2025,1,1)+timedelta(days=i)},{c},{c+1},{c-1},{c},100")
    return ("\n".join(lines) + "\n").encode()


class FixedSplitTests(unittest.TestCase):
    def test_disjoint_holdouts_without_unjustified_pooled_score(self):
        result = evaluate_fixed_splits(prices(), prices(),
                                       split_dates=["2025-03-20", "2025-04-05"],
                                       horizon=3)
        self.assertEqual(result["fold_count"], 2)
        self.assertFalse(result["overlapping_holdouts"])
        self.assertEqual(result["folds"][0]["holdout_end_date"], "2025-04-05")
        self.assertIsNone(result["folds"][1]["holdout_end_date"])
        self.assertIsNone(result["aggregate_independent_score"])
        self.assertFalse(result["trade_ready"])

    def test_first_fold_scores_only_labels_matured_before_next_split(self):
        from research_chronological_atr_experiment import evaluate_chronological_csv
        data = prices()
        split = "2025-03-20"
        boundary = "2025-04-05"
        bounded = evaluate_chronological_csv(
            data, data, split_date=split, holdout_end_date=boundary, horizon=10)
        # A 10-row forward outcome near the boundary matures after the fold.
        # All included labels must be known strictly before the next split.
        earlier = evaluate_chronological_csv(
            data, data, split_date=split, holdout_end_date="2025-04-02",
            horizon=10)
        self.assertGreaterEqual(bounded["events"], earlier["events"])
        self.assertLess(bounded["events"], 16)
        self.assertFalse(bounded["trade_ready"])

    def test_rejects_reordered_splits(self):
        with self.assertRaisesRegex(ValueError, "sorted"):
            evaluate_fixed_splits(prices(), prices(),
                                  split_dates=["2025-04-05", "2025-03-20"])


if __name__ == "__main__":
    unittest.main()
