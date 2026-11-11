"""Synthetic reference tests for Bartlett HAC of a paired mean."""
import math
import unittest
from research_paired_brier_hac import paired_brier_hac


def rows(diffs):
    # y=False, baseline=0, ATR=sqrt(d), so paired Brier difference=d
    return [{"severe": False, "baseline_probability": 0.0,
             "atr_probability": math.sqrt(d)} for d in diffs]


class HACTests(unittest.TestCase):
    def test_zero_lag_matches_population_variance_of_mean(self):
        result = paired_brier_hac(rows([0, 1, 0, 1]), lags=0)
        self.assertAlmostEqual(result["atr_minus_baseline_brier"], 0.5)
        self.assertAlmostEqual(result["hac_standard_error"], 0.25)

    def test_bartlett_lag_one_matches_hand_calculation(self):
        result = paired_brier_hac(rows([0, 1, 0, 1]), lags=1)
        # gamma0=.25, gamma1=-.1875, Bartlett weight=.5
        self.assertAlmostEqual(result["hac_standard_error"],
                               math.sqrt((.25 - .1875) / 4))

    def test_rejects_invalid_lag(self):
        with self.assertRaisesRegex(ValueError, "invalid_lags"):
            paired_brier_hac(rows([0, 1, 0, 1]), lags=True)


if __name__ == "__main__":
    unittest.main()
