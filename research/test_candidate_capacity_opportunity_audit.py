"""Focused tests for descriptive capacity-opportunity audit."""
import unittest
from candidate_capacity_opportunity_audit import summarize_capacity_opportunities


def candidate(symbol, day, outcome, baseline, filtered, selected=True):
    return {
        "symbol": symbol, "entry_day": day, "filter_selected": selected,
        "historical_net_return_pct_outcome_not_selection_input": outcome,
        "priority_decisions": {
            "baseline": {mode: baseline for mode in ("symbol_asc", "symbol_desc", "stable_hash")},
            "filtered": {mode: filtered for mode in ("symbol_asc", "symbol_desc", "stable_hash")}
        }
    }


class CapacityOpportunityAuditTests(unittest.TestCase):
    def test_simultaneous_competition_and_outcomes(self):
        rows = [
            candidate("AAA", 100, 2.0, "ACCEPTED", "ACCEPTED"),
            candidate("BBB", 100, 4.0, "CAPACITY_FULL", "CAPACITY_FULL"),
            candidate("CCC", 101, -3.0, "INSUFFICIENT_CASH", "NOT_IN_FILTERED_COHORT", False),
            candidate("DDD", 102, 1.0, "ACCEPTED", "ACCEPTED"),
        ]
        result = summarize_capacity_opportunities({"candidate_audit": rows})
        baseline = result["analysis"]["baseline"]["symbol_asc"]
        self.assertEqual(baseline["candidate_events_n"], 4)
        self.assertEqual(baseline["entry_days_with_simultaneous_accepted_and_capacity_rejected"], 1)
        self.assertEqual(baseline["by_decision"]["ACCEPTED"]["mean_historical_net_return_pct"], 1.5)
        self.assertEqual(baseline["by_decision"]["CAPACITY_FULL"]["mean_historical_net_return_pct"], 4.0)
        self.assertEqual(result["analysis"]["filtered"]["symbol_asc"]["candidate_events_n"], 3)
        self.assertFalse(result["trade_ready"])
        self.assertFalse(baseline["independent_predictive_validation"])

    def test_missing_decision_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "MISSING_PRIORITY_DECISION"):
            summarize_capacity_opportunities({"candidate_audit": [
                {"symbol": "AAA", "entry_day": 1, "priority_decisions": {}}
            ]})

    def test_duplicate_candidates_fail_closed(self):
        row = candidate("AAA", 1, 1.0, "ACCEPTED", "ACCEPTED")
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CANDIDATE"):
            summarize_capacity_opportunities({"candidate_audit": [row, row]})

    def test_invalid_filter_exclusion_fails_closed(self):
        row = candidate("AAA", 1, 1.0, "ACCEPTED", "NOT_IN_FILTERED_COHORT", True)
        with self.assertRaisesRegex(ValueError, "INVALID_FILTER_EXCLUSION"):
            summarize_capacity_opportunities({"candidate_audit": [row]})


if __name__ == "__main__":
    unittest.main()
