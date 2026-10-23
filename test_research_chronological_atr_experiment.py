"""Synthetic-only chronological integration tests."""
import unittest
from datetime import date, timedelta
from research_chronological_atr_experiment import evaluate_chronological_csv


def sample(n=110, shock=False):
    start = date(2025, 1, 1)
    lines = ["date,open,high,low,close,volume"]
    for i in range(n):
        c = 100 + i * .1
        if shock and i >= 90:
            c -= 20
        day = start + timedelta(days=i)
        lines.append(f"{day},{c},{c+1},{c-1},{c},100")
    return ("\n".join(lines) + "\n").encode()


class ExperimentTests(unittest.TestCase):
    def test_runs_only_with_mature_training_labels(self):
        result = evaluate_chronological_csv(sample(shock=True), sample(),
                                            split_date="2025-03-27", horizon=3)
        self.assertGreater(result["training_events"], 0)
        self.assertGreater(result["holdout_events"], 0)
        self.assertIn("atr_minus_baseline_brier", result)
        self.assertEqual(result["paired_diagnostics"]["events"], result["holdout_events"])
        self.assertFalse(result["paired_diagnostics"]["independent_events_assumed"])
        self.assertTrue(result["paired_diagnostics"]["outcome_window_coverage_complete"])
        self.assertEqual(result["paired_diagnostics"]["outcome_windows_supplied"],
                         result["holdout_events"])
        self.assertGreater(result["paired_diagnostics"]["overlapping_outcome_window_pairs"], 0)
        self.assertFalse(result["paired_diagnostics"]["uncertainty_interval_verified"])
        self.assertEqual(sum(result["paired_diagnostics"][key] for key in
                             ("atr_brier_better_events", "atr_brier_worse_events",
                              "equal_brier_events")), result["holdout_events"])
        self.assertFalse(result["independent_holdout_verified"])
        self.assertFalse(result["trade_ready"])


    def test_training_never_uses_labels_maturing_after_split(self):
        """Inspect the rows actually supplied to fitting at the split."""
        from unittest.mock import patch
        from research_atr_incremental_holdout_scoring import fit as real_fit

        captured = []

        def capture(rows):
            captured.extend(rows)
            return real_fit(rows)

        with patch("research_chronological_atr_experiment.fit",
                   side_effect=capture):
            evaluate_chronological_csv(
                sample(n=150), sample(n=150),
                split_date="2025-03-27", horizon=10)
        self.assertTrue(captured, "test requires nonempty training data")
        self.assertTrue(all(
            row["date"] < "2025-03-27"
            and row["label_available_date"] < "2025-03-27"
            for row in captured))


    def test_prediction_never_scores_pre_split_events(self):
        """Inspect actual rows reaching prediction, not just reported counts."""
        from unittest.mock import patch
        from research_atr_incremental_holdout_scoring import predict as real_predict

        captured = []

        def capture(model, rows):
            captured.extend(rows)
            return real_predict(model, rows)

        split = "2025-03-27"
        with patch("research_chronological_atr_experiment.predict",
                   side_effect=capture):
            evaluate_chronological_csv(
                sample(n=150), sample(n=150),
                split_date=split, horizon=10)
        self.assertTrue(captured, "fixture requires holdout predictions")
        self.assertTrue(all(row["date"] >= split for row in captured))


    def test_opt_in_exploratory_bootstrap_is_descriptive_only(self):
        result = evaluate_chronological_csv(
            sample(n=150, shock=True), sample(n=150),
            split_date="2025-03-27", horizon=3,
            exploratory_bootstrap=True, bootstrap_block_days=3,
            bootstrap_replicates=30, bootstrap_seed=7)
        boot = result["exploratory_bootstrap"]
        self.assertIsNotNone(boot)
        self.assertEqual(boot["events"], result["holdout_events"])
        self.assertFalse(boot["interval_validated_for_inference"])
        self.assertFalse(boot["trade_ready"])
        self.assertFalse(result["independent_holdout_verified"])


    def test_opt_in_block_sensitivity_uses_fixed_lengths(self):
        result = evaluate_chronological_csv(
            sample(n=150, shock=True), sample(n=150),
            split_date="2025-03-27", horizon=3,
            bootstrap_sensitivity_lengths=(3, 5),
            bootstrap_replicates=20, bootstrap_seed=7)
        sensitivity = result["bootstrap_sensitivity"]
        self.assertEqual(sensitivity["block_lengths"], [3, 5])
        self.assertEqual(len(sensitivity["results"]), 2)
        self.assertFalse(sensitivity["intervals_validated_for_inference"])
        self.assertFalse(result["trade_ready"])

    def test_bootstrap_disabled_by_default(self):
        result = evaluate_chronological_csv(
            sample(), sample(), split_date="2025-03-27", horizon=3)
        self.assertIsNone(result["exploratory_bootstrap"])

    def test_rejects_insufficient_embargo(self):
        with self.assertRaisesRegex(ValueError, "training_labels_not_available"):
            evaluate_chronological_csv(sample(), sample(),
                                       split_date="2025-03-27", horizon=10,
                                       embargo_seconds=86400 * 20)


if __name__ == "__main__":
    unittest.main()
