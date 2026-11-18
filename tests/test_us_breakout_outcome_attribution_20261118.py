"""Synthetic-only aggregate outcome tests."""
import unittest
from research.us_breakout_outcome_attribution_20261118 import aggregate_watch_outcomes

T = ["2026-11-17T14:00:00Z", "2026-11-17T15:00:00Z",
     "2026-11-17T16:00:00Z", "2026-11-17T17:00:00Z"]
def candidate(name, prices):
    return {"symbol": name, "historical_friction_usd": 100,
            "observations": [{"observed_utc": t, "close_usd": p}
                             for t, p in zip(T, prices)]}

class OutcomeAttributionTests(unittest.TestCase):
    def test_empty(self):
        x = aggregate_watch_outcomes([])
        self.assertEqual(x["total"], 0)
        self.assertFalse(x["trade_ready"])

    def test_stage_counts(self):
        x = aggregate_watch_outcomes([
            candidate("A", [99, 99]),
            candidate("B", [99, 101]),
            candidate("C", [99, 101, 100]),
            candidate("D", [99, 101, 100, 102])])
        self.assertEqual(x["breakout_observed_total"], 3)
        self.assertEqual(x["retest_and_reclaim_observed_total"], 1)
        self.assertEqual(x["verified_trade_opportunities"], 0)

    def test_no_private_identifiers_in_aggregate(self):
        x = aggregate_watch_outcomes([candidate("PRIVATE_SYMBOL", [99, 101])])
        self.assertNotIn("PRIVATE_SYMBOL", str(x))
        self.assertNotIn("2026-11-17", str(x))

    def test_duplicate_symbol_blocked(self):
        x = aggregate_watch_outcomes([candidate("A", [99]), candidate("A", [101])])
        self.assertEqual(x["status"], "BLOCKED")

    def test_invalid_record_blocked(self):
        self.assertEqual(aggregate_watch_outcomes([None])["status"], "BLOCKED")

    def test_missing_symbol_blocked(self):
        x = aggregate_watch_outcomes([{"observations": []}])
        self.assertEqual(x["status"], "BLOCKED")

    def test_missing_observations_not_success(self):
        x = aggregate_watch_outcomes([candidate("A", [])])
        self.assertEqual(x["breakout_observed_total"], 0)

    def test_invalid_time_counted_as_blocked(self):
        x = aggregate_watch_outcomes([{"symbol": "A", "historical_friction_usd": 100,
             "observations": [{"observed_utc": "bad", "close_usd": 101}]}])
        self.assertEqual(x["counts"]["BLOCKED"], 1)

    def test_no_trade_permissions(self):
        x = aggregate_watch_outcomes([candidate("A", [99, 101, 100, 102])])
        self.assertFalse(x["notify"])
        self.assertFalse(x["automatic_orders"])
        self.assertFalse(x["order_placement_enabled"])

    def test_nonlist_blocked(self):
        self.assertEqual(aggregate_watch_outcomes({})["status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
