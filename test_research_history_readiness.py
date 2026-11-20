import unittest
from research_history_readiness import assess_history_readiness

S = [
    {"id": "a", "decision": "SELECTED", "observed_utc": "2026-01-01T00:00:00Z"},
    {"id": "b", "decision": "REJECTED", "observed_utc": "2026-01-01T00:00:00Z"},
]
O = [
    {"id": "a", "observed_utc": "2026-01-10T00:00:00Z", "return_pct": 5},
    {"id": "b", "observed_utc": "2026-01-10T00:00:00Z", "return_pct": -4},
]

class HistoryReadinessTests(unittest.TestCase):
    def test_missing_outcome_blocks(self):
        r = assess_history_readiness(S, O[:1])
        self.assertEqual(r["reason"], "MISSING_HISTORICAL_OUTCOMES")
        self.assertEqual(r["coverage"]["outcome_coverage_fraction"], .5)

    def test_full_supplied_sample_still_unverified(self):
        r = assess_history_readiness(S, O)
        self.assertEqual(r["reason"], "UNIVERSE_AND_PROVENANCE_UNVERIFIED")
        self.assertFalse(r["backtest_validated"])
        self.assertFalse(r["trade_ready"])

    def test_selected_only_sample_is_not_enough(self):
        r = assess_history_readiness(S[:1], O[:1])
        self.assertEqual(r["reason"], "NO_REJECTED_SIGNALS_REPRESENTED")

    def test_empty_universe_blocks(self):
        self.assertEqual(assess_history_readiness([], [])["reason"],
                         "EMPTY_SIGNAL_UNIVERSE")

    def test_bad_outcome_blocks(self):
        self.assertEqual(assess_history_readiness(S, [{**O[0], "return_pct": None}])["reason"],
                         "INVALID_OUTCOME_VALUE")

if __name__ == "__main__":
    unittest.main()
