"""Offline tests for rejected opportunity attribution."""
import unittest
from integrated_rejected_opportunity_attribution import attribute

def trade(ident, allocation):
    return {"id": ident, "entry_date": "2026-11-02", "exit_date": "2026-11-10",
            "allocation_eur": allocation, "research_only": True, "trade_ready": False}

class RejectedOpportunityTests(unittest.TestCase):
    def test_unknown_future_outcome_stays_unknown(self):
        result = attribute([trade("A", 40000), trade("B", 20000)])
        self.assertEqual(result["rejected_count"], 1)
        self.assertFalse(result["rejected_outcomes"][0]["outcome_known"])
        self.assertIsNone(result["rejected_outcomes"][0]["foregone_net_pnl_eur"])
        self.assertFalse(result["trade_ready"])

    def test_verified_later_outcome_attributed(self):
        outcomes = {"B": {"observed_after_exit": True, "source_verified": True,
                          "gross_pnl_eur": 400, "total_costs_eur": 20}}
        result = attribute([trade("A", 40000), trade("B", 20000)], outcomes)
        self.assertEqual(result["rejected_outcomes"][0]["foregone_net_pnl_eur"], "380")
        self.assertFalse(result["causal_opportunity_cost_proven"])

    def test_early_outcome_blocked(self):
        outcomes = {"B": {"observed_after_exit": False, "source_verified": True,
                          "gross_pnl_eur": 400, "total_costs_eur": 20}}
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_FUTURE_OUTCOME"):
            attribute([trade("A", 40000), trade("B", 20000)], outcomes)

    def test_unverified_source_blocked(self):
        outcomes = {"B": {"observed_after_exit": True, "source_verified": False,
                          "gross_pnl_eur": 400, "total_costs_eur": 20}}
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_FUTURE_OUTCOME"):
            attribute([trade("A", 40000), trade("B", 20000)], outcomes)

    def test_unknown_outcome_id_blocked(self):
        with self.assertRaisesRegex(ValueError, "UNKNOWN_OUTCOME_ID"):
            attribute([trade("A", 1000)], {"C": {}})

    def test_negative_costs_blocked(self):
        outcomes = {"B": {"observed_after_exit": True, "source_verified": True,
                          "gross_pnl_eur": 400, "total_costs_eur": -20}}
        with self.assertRaisesRegex(ValueError, "INVALID_OUTCOME_COSTS"):
            attribute([trade("A", 40000), trade("B", 20000)], outcomes)

    def test_no_rejections(self):
        result = attribute([trade("A", 1000)])
        self.assertEqual(result["rejected_count"], 0)
        self.assertEqual(result["rejected_outcomes"], [])

if __name__ == "__main__":
    unittest.main()
