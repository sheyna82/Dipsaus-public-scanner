"""Synthetic matched-cohort benchmark tests."""
import unittest
from decimal import Decimal
from research_swing_score_benchmark import compare_rankings


def cohort():
    return {"cohort_id": "fixture-day-1", "candidates": [
        {"ticker": "A", "eligible": True, "hypothesis_score": 9,
         "baseline_score": 1, "net_return_pct": 5},
        {"ticker": "B", "eligible": True, "hypothesis_score": 1,
         "baseline_score": 9, "net_return_pct": -2},
        {"ticker": "C", "eligible": True, "hypothesis_score": 2,
         "baseline_score": 2, "net_return_pct": 1},
    ]}


class BenchmarkTests(unittest.TestCase):
    def test_hypothesis_vs_baseline_same_cohort(self):
        result = compare_rankings([cohort()], slots=1)
        self.assertEqual(result["cohorts"][0]["hypothesis_tickers"], ["A"])
        self.assertEqual(result["cohorts"][0]["baseline_tickers"], ["B"])
        self.assertEqual(Decimal(result["mean_difference_percentage_points"]), 7)
        self.assertFalse(result["predictive_edge_proven"])

    def test_same_selection_no_artificial_edge(self):
        result = compare_rankings([cohort()], slots=3)
        self.assertEqual(Decimal(result["mean_difference_percentage_points"]), 0)

    def test_duplicate_ticker_rejected(self):
        x = cohort()
        x["candidates"][1]["ticker"] = "A"
        with self.assertRaisesRegex(ValueError, "duplicate_or_invalid_ticker"):
            compare_rankings([x])

    def test_ineligible_excluded(self):
        x = cohort()
        x["candidates"][0]["eligible"] = False
        result = compare_rankings([x], slots=1)
        self.assertNotIn("A", result["cohorts"][0]["hypothesis_tickers"])

    def test_invalid_return_rejected(self):
        x = cohort()
        x["candidates"][0]["net_return_pct"] = "NaN"
        with self.assertRaisesRegex(ValueError, "invalid_numeric"):
            compare_rankings([x])

    def test_not_enough_candidates_rejected(self):
        x = cohort()
        x["candidates"][1]["eligible"] = False
        x["candidates"][2]["eligible"] = False
        with self.assertRaisesRegex(ValueError, "insufficient_matched"):
            compare_rankings([x])


if __name__ == "__main__":
    unittest.main()
