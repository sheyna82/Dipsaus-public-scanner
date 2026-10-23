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
        self.assertFalse(result["independent_holdout_verified"])
        self.assertFalse(result["trade_ready"])

    def test_rejects_insufficient_embargo(self):
        with self.assertRaisesRegex(ValueError, "training_labels_not_available"):
            evaluate_chronological_csv(sample(), sample(),
                                       split_date="2025-03-27", horizon=10,
                                       embargo_seconds=86400 * 20)


if __name__ == "__main__":
    unittest.main()
