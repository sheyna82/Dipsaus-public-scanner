"""Synthetic regression tests for paired holdout diagnostic accounting."""
import unittest

from research_paired_holdout_diagnostics import paired_holdout_diagnostics


class PairedHoldoutDiagnosticsTests(unittest.TestCase):
    def test_counts_and_direction_of_loss_differences(self):
        rows = [
            {"severe": True, "baseline_probability": .2, "atr_probability": .8},
            {"severe": False, "baseline_probability": .2, "atr_probability": .8},
            {"severe": True, "baseline_probability": .5, "atr_probability": .5},
        ]
        result = paired_holdout_diagnostics(rows)
        self.assertEqual(result["events"], 3)
        self.assertEqual(result["atr_brier_better_events"], 1)
        self.assertEqual(result["atr_brier_worse_events"], 1)
        self.assertEqual(result["equal_brier_events"], 1)
        self.assertEqual(result["non_tied_events"], 2)
        self.assertAlmostEqual(result["atr_brier_better_fraction"], 1 / 3)
        self.assertAlmostEqual(result["atr_brier_worse_fraction"], 1 / 3)
        self.assertAlmostEqual(result["atr_brier_tie_fraction"], 1 / 3)
        self.assertAlmostEqual(result["atr_minus_baseline_brier_unrounded"], 0)
        self.assertAlmostEqual(result["atr_minus_baseline_log_loss_unrounded"], 0)
        self.assertFalse(result["independent_events_assumed"])
        self.assertFalse(result["uncertainty_interval_verified"])
        self.assertFalse(result["trade_ready"])


    def test_overlapping_outcome_windows_reported(self):
        rows = [
            {"severe": False, "baseline_probability": .2,
             "atr_probability": .3, "event_date": "2025-01-01",
             "label_available_date": "2025-01-10"},
            {"severe": True, "baseline_probability": .4,
             "atr_probability": .5, "event_date": "2025-01-05",
             "label_available_date": "2025-01-15"},
            {"severe": False, "baseline_probability": .2,
             "atr_probability": .3, "event_date": "2025-02-01",
             "label_available_date": "2025-02-10"},
        ]
        result = paired_holdout_diagnostics(rows)
        self.assertEqual(result["overlapping_outcome_window_pairs"], 1)
        self.assertTrue(result["outcome_window_coverage_complete"])
        self.assertFalse(result["independent_events_assumed"])

    def test_incomplete_outcome_window_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete_outcome_window"):
            paired_holdout_diagnostics([
                {"severe": False, "baseline_probability": .2,
                 "atr_probability": .3, "event_date": "2025-01-01"}
            ])

    def test_invalid_probability_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_probability"):
            paired_holdout_diagnostics([
                {"severe": False, "baseline_probability": .3,
                 "atr_probability": float("nan")}
            ])

    def test_empty_holdout_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty_holdout"):
            paired_holdout_diagnostics([])


if __name__ == "__main__":
    unittest.main()
