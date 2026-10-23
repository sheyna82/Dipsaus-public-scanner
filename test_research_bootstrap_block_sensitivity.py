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
        self.assertFalse(result["intervals_validated_for_inference"])
        self.assertFalse(result["trade_ready"])

    def test_duplicate_block_lengths_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_block_lengths"):
            bootstrap_block_sensitivity(sample(), block_lengths=(3, 3),
                                        replicates=20)


if __name__ == "__main__":
    unittest.main()
