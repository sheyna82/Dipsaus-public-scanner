"""Synthetic checks only: no historical test outcomes consumed."""
import unittest
from research_atr_incremental_holdout_scoring import fit, predict, evaluate


class IncrementalATRHoldoutScoringTests(unittest.TestCase):
    def event(self, structure, market, atr, severe):
        return {"structure_above_20d_mean": structure,
                "market_20d_positive": market,
                "atr_expanding": atr, "severe": severe}

    def test_paired_predictions_and_no_trade_gate(self):
        training = [self.event(True, True, False, True),
                    self.event(True, True, True, False),
                    self.event(True, True, True, False)]
        holdout = [self.event(True, True, False, True),
                   self.event(True, True, True, False)]
        model = fit(training)
        result = evaluate(predict(model, holdout))
        self.assertEqual(result["events"], 2)
        self.assertEqual(result["severe_events"], 1)
        self.assertLess(result["atr_brier"], result["baseline_brier"])
        self.assertFalse(result["independent_holdout_verified"])
        self.assertFalse(result["trade_ready"])

    def test_unknown_cells_use_training_prior(self):
        training = [self.event(True, True, True, True)]
        holdout = [self.event(False, False, False, False)]
        predictions = predict(fit(training), holdout)
        self.assertTrue(predictions[0]["baseline_fallback"])
        self.assertTrue(predictions[0]["atr_fallback"])
        self.assertEqual(predictions[0]["baseline_probability"], 2 / 3)

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            fit([])
        with self.assertRaises(ValueError):
            fit([self.event(1, True, False, True)])
        with self.assertRaises(ValueError):
            evaluate([])


if __name__ == "__main__":
    unittest.main()
