"""Synthetic sensitivity tests; never interpret these as market evidence."""
import unittest
from research_bootstrap_block_sensitivity import bootstrap_block_sensitivity


def sample():
    return [
        {"event_date": f"2025-01-{day:02d}", "severe": day % 2 == 0,
         "baseline_probability": .5, "atr_probability": .5}
        for day in range(1, 16)
    ]


class BootstrapBlockSensitivityTests(unittest.TestCase):
    def test_fixed_block_grid_reports_all_intervals(self):
        result = bootstrap_block_sensitivity(
            sample(), block_lengths=(3, 5, 8), replicates=30, seed=17)
        self.assertEqual(result["block_lengths"], [3, 5, 8])
        self.assertEqual(len(result["results"]), 3)
        self.assertTrue(all(r["exploratory_interval"] == [0, 0]
                            for r in result["results"]))
        self.assertFalse(result["all_intervals_exclude_zero"])
        self.assertTrue(result["all_brier_weighting_agrees"])
        self.assertFalse(result["opposite_brier_weighting_conclusions"])
        self.assertFalse(result["opposite_log_loss_weighting_conclusions"])
        self.assertTrue(result["all_log_loss_weighting_agrees"])
        self.assertEqual(len(result["weighting_sensitivity"]), 3)
        self.assertEqual(result["weighting_sensitivity"][0]["event_weighted_brier_sign"],
                         "crosses_zero")
        self.assertFalse(result["intervals_validated_for_inference"])
        self.assertFalse(result["trade_ready"])


    def test_opposite_weighting_conclusions_detected_on_synthetic_data(self):
        # One high-volume date favors ATR; many low-volume dates favor baseline.
        # Each forecast pair is kept together within its observed date.
        sample = []
        for day in range(1, 21):
            count = 100 if day == 1 else 1
            for _ in range(count):
                sample.append({
                    "event_date": f"2025-01-{day:02d}",
                    "severe": False,
                    "baseline_probability": .9 if day == 1 else .1,
                    "atr_probability": .1 if day == 1 else .9,
                })
        result = bootstrap_block_sensitivity(
            sample, block_lengths=(1,), replicates=1000, seed=13)
        self.assertTrue(result["opposite_brier_weighting_conclusions"])
        self.assertTrue(result["opposite_log_loss_weighting_conclusions"])
        self.assertFalse(result["all_brier_weighting_agrees"])
        self.assertFalse(result["all_log_loss_weighting_agrees"])
        self.assertFalse(result["intervals_validated_for_inference"])

    def test_duplicate_block_lengths_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_block_lengths"):
            bootstrap_block_sensitivity(sample(), block_lengths=(3, 3),
                                        replicates=20)


if __name__ == "__main__":
    unittest.main()
