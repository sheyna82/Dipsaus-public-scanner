"""Offline synthetic integration tests for swing research pipeline."""
import unittest
from research_swing_pipeline import evaluate_research_batch


def candidate(ticker, score, end=105, recorded="2026-11-02", eligible=True):
    provenance = {"ticker": ticker, "score": score,
                  "source_id": "synthetic-fixture", "strategy_version": "test-v1",
                  "signal_id": "fixture-" + ticker,
                  "score_source_available_at": recorded + "T14:00:00Z",
                  "signal_created_at": recorded + "T14:01:00Z",
                  "entry_at": "2026-11-02T14:05:00Z",
                  "outcome_source_available_at": "2026-11-10T21:00:00Z"}
    return {"ticker": ticker, "score": score, "entry_price": 100,
            "provenance": provenance,
            "daily_closes": [101, 102, 103, 104, end],
            "recorded_day": recorded, "eligible": eligible}


class PipelineTests(unittest.TestCase):
    def run_batch(self, items, **kwargs):
        return evaluate_research_batch(
            items, entry_day="2026-11-02", outcome_day="2026-11-10",
            capital=3500, **kwargs)

    def test_portfolio_and_rank_consistent(self):
        result = self.run_batch([candidate("HIGH", 9, 105),
                                 candidate("LOW", 1, 95)])
        self.assertEqual(result["portfolio"]["selected"][0]["ticker"], "HIGH")
        self.assertEqual(result["portfolio"]["portfolio_net_pnl"], "175.00")
        self.assertEqual(result["ranking"]["mean_top_minus_bottom_pct_points"], "10.0000")
        self.assertFalse(result["source_provenance_independently_verified"])

    def test_ineligible_excluded_from_rank(self):
        result = self.run_batch([candidate("HIGH", 9),
                                 candidate("LOW", 1, eligible=False)])
        self.assertEqual(result["ranking"]["eligible_rows"], 1)

    def test_missing_provenance_rejected(self):
        item = candidate("A", 1)
        del item["provenance"]
        with self.assertRaisesRegex(ValueError, "missing_candidate_provenance"):
            self.run_batch([item])

    def test_provenance_score_mismatch_rejected(self):
        item = candidate("A", 1)
        item["provenance"]["score"] = 2
        with self.assertRaisesRegex(ValueError, "provenance_candidate_mismatch"):
            self.run_batch([item])

    def test_future_recorded_score_rejected(self):
        with self.assertRaisesRegex(ValueError, "future_information_or_invalid_order"):
            self.run_batch([candidate("A", 1, recorded="2026-11-03")])

    def test_invalid_outcome_order_rejected(self):
        with self.assertRaisesRegex(ValueError, "outcome_must_follow_entry"):
            evaluate_research_batch([], entry_day="2026-11-02",
                                    outcome_day="2026-11-02")

    def test_costs_reduce_realized_portfolio_pnl(self):
        items = [candidate("A", 3)]
        free = self.run_batch(items)
        costly = self.run_batch(items, spread_bps=10,
                                slippage_bps=5, commission_bps=2)
        from decimal import Decimal
        self.assertLess(Decimal(costly["portfolio"]["portfolio_net_pnl"]),
                        Decimal(free["portfolio"]["portfolio_net_pnl"]))


if __name__ == "__main__":
    unittest.main()
