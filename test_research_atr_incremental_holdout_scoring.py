"""Synthetic checks only: no historical test outcomes consumed."""
import unittest
from research_atr_incremental_holdout_scoring import fit, predict, evaluate, forecast


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

    def test_scored_and_prospective_forecasts_match(self):
        model = fit([self.event(True, True, True, False),
                     self.event(False, True, False, True)])
        labelled = [self.event(True, True, True, True)]
        without_label = [{k: v for k, v in labelled[0].items() if k != "severe"}]
        scored = predict(model, labelled)[0]
        prospective = forecast(model, without_label)[0]
        for key in ("baseline_probability", "atr_probability",
                    "baseline_fallback", "atr_fallback"):
            self.assertEqual(scored[key], prospective[key])
        self.assertEqual(scored["severe"], True)

    def test_forecast_does_not_require_future_outcomes(self):
        model = fit([self.event(True, True, True, False)])
        features = {"structure_above_20d_mean": True,
                    "market_20d_positive": True, "atr_expanding": True}
        result = forecast(model, [features])
        self.assertEqual(len(result), 1)
        self.assertNotIn("severe", result[0])
        self.assertFalse(result[0]["trade_ready"])
        self.assertEqual(result[0]["atr_probability"], 1 / 3)

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
