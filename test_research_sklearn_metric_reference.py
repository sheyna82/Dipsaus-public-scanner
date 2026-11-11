"""Synthetic parity checks against documented sklearn binary scoring formulas.

No external dependency installed. The 0.01/0.99 log clipping is an
explicit DIPSAUS choice, not sklearn's machine-epsilon clipping.
"""
import math
import unittest
from research_atr_incremental_holdout_scoring import evaluate


class ProbabilityScoringReferenceTests(unittest.TestCase):
    def test_binary_brier_and_log_loss_formula_parity(self):
        outcomes = [False, True, True, False]
        baseline = [0.1, 0.9, 0.8, 0.3]
        atr = [0.2, 0.7, 0.6, 0.4]
        rows = [{"severe": y, "baseline_probability": p,
                 "atr_probability": q, "baseline_fallback": False,
                 "atr_fallback": False}
                for y, p, q in zip(outcomes, baseline, atr)]
        report = evaluate(rows)
        for name, values in (("baseline", baseline), ("atr", atr)):
            brier = sum((p - int(y)) ** 2 for p, y in zip(values, outcomes)) / 4
            logloss = -sum(int(y) * math.log(p) +
                           (1 - int(y)) * math.log(1 - p)
                           for p, y in zip(values, outcomes)) / 4
            self.assertAlmostEqual(report[name + "_brier"], brier, places=7)
            self.assertAlmostEqual(report[name + "_log_loss"], logloss, places=7)

    def test_clipping_differs_from_sklearn_default(self):
        rows = [{"severe": True, "baseline_probability": 0.0,
                 "atr_probability": 1.0, "baseline_fallback": False,
                 "atr_fallback": False}]
        report = evaluate(rows)
        self.assertAlmostEqual(report["baseline_log_loss"], -math.log(0.01), places=7)
        self.assertAlmostEqual(report["atr_log_loss"], -math.log(0.99), places=7)
        self.assertEqual(report["baseline_brier"], 1.0)
        self.assertEqual(report["atr_brier"], 0.0)


if __name__ == "__main__":
    unittest.main()
