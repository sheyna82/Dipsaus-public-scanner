"""Synthetic integration tests for hypothesis scoring and swing evaluation."""
import unittest
from research_swing_hypothesis_score import RECIPES, score_candidate
from research_swing_hypothesis_pipeline import evaluate_hypothesis_lane


def candidate(ticker, factor, lane="technical_recovery"):
    factors = {name: factor for name in RECIPES[lane]}
    score = score_candidate(lane, factors)["score"]
    return {"ticker": ticker, "lane": lane, "factors": factors,
            "entry_price": 100, "daily_closes": [101, 102, 103, 104, 105],
            "recorded_day": "2026-11-02", "eligible": True,
            "provenance": {
                "ticker": ticker, "score": score,
                "source_id": "synthetic-fixture", "strategy_version": "hypothesis-v0",
                "signal_id": "synthetic-" + ticker,
                "score_source_available_at": "2026-11-02T14:00:00Z",
                "signal_created_at": "2026-11-02T14:01:00Z",
                "entry_at": "2026-11-02T14:05:00Z",
                "outcome_source_available_at": "2026-11-10T21:00:00Z"}}


class HypothesisPipelineTests(unittest.TestCase):
    def evaluate(self, items, **kwargs):
        return evaluate_hypothesis_lane(
            items, lane="technical_recovery",
            entry_day="2026-11-02", outcome_day="2026-11-10",
            capital=3500, **kwargs)

    def test_valid_cohort_integrates(self):
        result = self.evaluate([candidate("A", "0.9"),
                                candidate("B", "0.1")])
        self.assertEqual(result["analysis"]["portfolio"]["selected"][0]["ticker"], "A")
        self.assertFalse(result["predictive_edge_proven"])

    def test_score_tampering_rejected(self):
        x = candidate("A", "0.9")
        x["factors"]["relative_strength_5d"] = "0.1"
        with self.assertRaisesRegex(ValueError, "score_not_previously_recorded"):
            self.evaluate([x])

    def test_mixed_lanes_rejected(self):
        with self.assertRaisesRegex(ValueError, "mixed_uncalibrated_lanes"):
            self.evaluate([candidate("A", "0.9"),
                           candidate("B", "0.5", "event_catalyst")])

    def test_missing_provenance_rejected(self):
        x = candidate("A", "0.9")
        del x["provenance"]
        with self.assertRaisesRegex(ValueError, "score_not_previously_recorded"):
            self.evaluate([x])

    def test_cannot_disable_provenance(self):
        with self.assertRaisesRegex(ValueError, "provenance_cannot_be_disabled"):
            self.evaluate([candidate("A", "0.9")], require_provenance=False)


if __name__ == "__main__":
    unittest.main()
