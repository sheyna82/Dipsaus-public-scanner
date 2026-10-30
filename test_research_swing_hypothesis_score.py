"""Synthetic unit tests for transparent swing score hypotheses."""
import unittest
from decimal import Decimal
from research_swing_hypothesis_score import (
    RECIPES, score_candidate,
)


def factors(lane, value="0.5"):
    return {name: value for name in RECIPES[lane]}


class HypothesisScoreTests(unittest.TestCase):
    def test_equal_factors_score_fifty(self):
        for lane in RECIPES:
            with self.subTest(lane=lane):
                result = score_candidate(lane, factors(lane))
                self.assertEqual(Decimal(result["score"]), Decimal(50))
                self.assertFalse(result["predictive_edge_proven"])

    def test_all_zero_and_all_one(self):
        for lane in RECIPES:
            self.assertEqual(Decimal(score_candidate(lane, factors(lane, "0"))["score"]), 0)
            self.assertEqual(Decimal(score_candidate(lane, factors(lane, "1"))["score"]), 100)

    def test_recovery_relative_strength_matters(self):
        x = factors("technical_recovery", "0")
        x["relative_strength_5d"] = "1"
        self.assertEqual(Decimal(score_candidate("technical_recovery", x)["score"]), 30)

    def test_event_materiality_matters(self):
        x = factors("event_catalyst", "0")
        x["catalyst_materiality"] = "1"
        self.assertEqual(Decimal(score_candidate("event_catalyst", x)["score"]), 30)

    def test_missing_factor_rejected(self):
        x = factors("technical_recovery")
        del x["trend_stability"]
        with self.assertRaisesRegex(ValueError, "missing_or_unexpected"):
            score_candidate("technical_recovery", x)

    def test_out_of_range_rejected(self):
        x = factors("event_catalyst")
        x["price_confirmation"] = "1.1"
        with self.assertRaisesRegex(ValueError, "factor_out_of_range"):
            score_candidate("event_catalyst", x)

    def test_non_finite_rejected(self):
        x = factors("event_catalyst")
        x["price_confirmation"] = "NaN"
        with self.assertRaisesRegex(ValueError, "factor_out_of_range"):
            score_candidate("event_catalyst", x)

    def test_unknown_lane_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown_research_lane"):
            score_candidate("other", {})


if __name__ == "__main__":
    unittest.main()
