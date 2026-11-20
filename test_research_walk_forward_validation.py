import unittest
from research_walk_forward_validation import evaluate_walk_forward as evaluate

FEATURE = dict(net_profit_eur=200, net_rr=3, relative_volume=1.5,
               market_context=.8, sector_context=.8,
               risk_inputs=dict(bid=99.9, ask=100,
                                average_daily_turnover_eur=2000000,
                                relative_volume=1.5,
                                earnings_calendar_checked=True,
                                sessions_until_earnings=9))

def rec(id, features_at, outcome_at, outcome=3):
    return dict(id=id, features={**FEATURE, "id": id},
                features_observed_utc=features_at,
                outcome_observed_utc=outcome_at,
                outcome_return_pct=outcome)

class WalkForwardValidationTests(unittest.TestCase):
    def test_strict_split_and_cross_cutoff_exclusion(self):
        r = evaluate([
            rec("train", "2026-01-01T12:00:00Z", "2026-01-10T12:00:00Z", 2),
            rec("cross", "2026-01-20T12:00:00Z", "2026-02-02T12:00:00Z", 9),
            rec("test", "2026-02-02T12:00:00Z", "2026-02-10T12:00:00Z", -1),
        ], cutoff_utc="2026-02-01T00:00:00Z")
        self.assertEqual(r["train"]["observations"], 1)
        self.assertEqual(r["test"]["observations"], 1)
        self.assertEqual(r["excluded_cross_cutoff"], 1)
        self.assertEqual(r["test"]["mean_observed_return_pct"], -1)
        self.assertFalse(r["trade_ready"])

    def test_future_features_after_outcome_block(self):
        r = evaluate([rec("a", "2026-02-10T00:00:00Z",
                          "2026-02-09T00:00:00Z")],
                     cutoff_utc="2026-02-01T00:00:00Z")
        self.assertEqual(r["status"], "HISTORICAL_INPUT_BLOCKED")

    def test_naive_timestamp_blocks(self):
        r = evaluate([rec("a", "2026-01-01T00:00:00",
                          "2026-01-09T00:00:00Z")],
                     cutoff_utc="2026-02-01T00:00:00Z")
        self.assertEqual(r["status"], "HISTORICAL_INPUT_BLOCKED")

    def test_duplicate_id_blocks(self):
        a = rec("a", "2026-01-01T00:00:00Z", "2026-01-09T00:00:00Z")
        self.assertEqual(evaluate([a, a], cutoff_utc="2026-02-01T00:00:00Z")["status"],
                         "HISTORICAL_INPUT_BLOCKED")

    def test_missing_outcome_blocks(self):
        a = rec("a", "2026-01-01T00:00:00Z", "2026-01-09T00:00:00Z")
        del a["outcome_return_pct"]
        self.assertEqual(evaluate([a], cutoff_utc="2026-02-01T00:00:00Z")["status"],
                         "HISTORICAL_INPUT_BLOCKED")

    def test_invalid_cutoff_blocks(self):
        self.assertEqual(evaluate([], cutoff_utc="2026-02-01")["status"],
                         "HISTORICAL_INPUT_BLOCKED")

    def test_failed_financial_gate_excluded_from_mean(self):
        a = rec("a", "2026-01-01T00:00:00Z", "2026-01-09T00:00:00Z")
        a["features"]["net_profit_eur"] = 149
        r = evaluate([a], cutoff_utc="2026-02-01T00:00:00Z")
        self.assertEqual(r["train"]["research_review_candidates"], 0)
        self.assertIsNone(r["train"]["mean_observed_return_pct"])

if __name__ == "__main__":
    unittest.main()
