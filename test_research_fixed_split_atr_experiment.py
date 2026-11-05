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


    def test_fold_excludes_unmatured_labels_at_boundary(self):
        """Inspect the actual scored events, not only their total count."""
        from unittest.mock import patch
        from research_chronological_atr_experiment import evaluate_chronological_csv
        from research_atr_incremental_holdout_scoring import predict as real_predict

        observed = []

        def capture(model, rows):
            observed.extend(rows)
            return real_predict(model, rows)

        data = prices()
        with patch("research_chronological_atr_experiment.predict",
                   side_effect=capture):
            evaluate_chronological_csv(
                data, data, split_date="2025-03-20",
                holdout_end_date="2025-04-05", horizon=10)
        self.assertTrue(observed, "test requires actual scored holdout rows")
        for row in observed:
            self.assertLess(row["label_available_date"], "2025-04-05")
            self.assertGreaterEqual(row["date"], "2025-03-20")
            self.assertLess(row["date"], "2025-04-05")


    def test_exact_boundary_maturity_is_excluded(self):
        """The next fold's opening date is not part of the prior fold."""
        from unittest.mock import patch
        from research_chronological_atr_experiment import evaluate_chronological_csv
        from research_daily_feature_label_join import join_features_and_labels
        from research_atr_incremental_holdout_scoring import predict as real_predict

        data = prices()
        boundary = "2025-04-05"
        candidates = join_features_and_labels(data, horizon=10)
        exact = [row for row in candidates
                 if row["date"] >= "2025-03-20"
                 and row["label_available_date"] == boundary]
        self.assertTrue(exact, "fixture must contain an exact-boundary label")
        scored_dates = []

        def capture(model, rows):
            scored_dates.extend(row["date"] for row in rows)
            return real_predict(model, rows)

        with patch("research_chronological_atr_experiment.predict",
                   side_effect=capture):
            evaluate_chronological_csv(
                data, data, split_date="2025-03-20",
                holdout_end_date=boundary, horizon=10)
        self.assertTrue(scored_dates)
        self.assertTrue(all(row["date"] not in scored_dates for row in exact))

    def test_rejects_reordered_splits(self):
        with self.assertRaisesRegex(ValueError, "sorted"):
            evaluate_fixed_splits(prices(), prices(),
                                  split_dates=["2025-04-05", "2025-03-20"])


if __name__ == "__main__":
    unittest.main()
