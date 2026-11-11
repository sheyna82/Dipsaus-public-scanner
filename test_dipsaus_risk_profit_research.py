import unittest
from dipsaus_risk_profit_research import combine_research


def risk(state):
    return {"state": state, "research_only": True, "trade_ready": False,
            "notify": False, "sell_recommendation": False}


class RiskProfitResearchTests(unittest.TestCase):
    def test_combined_review_never_sells(self):
        result = combine_research(risk("DEEPER_SUPPORT_BREACH_REVIEW"),
                                  {"status": "PROFIT_GIVEBACK_OBSERVED"})
        self.assertTrue(result["joint_review"])
        self.assertTrue(result["risk_and_profit_both_need_review"])
        self.assertFalse(result["automatic_sell"])
        self.assertFalse(result["stop_order_created"])
        self.assertFalse(result["notify"])
        self.assertFalse(result["trade_ready"])

    def test_no_proximity_only_exit(self):
        result = combine_research(risk("ABOVE_REFERENCE_SUPPORT"),
                                  {"status": "NO_PROFIT_CONTEXT"})
        self.assertFalse(result["joint_review"])

    def test_unknown_context_fails_closed(self):
        self.assertIsNone(combine_research(risk("ABOVE_REFERENCE_SUPPORT"), {}))
        self.assertIsNone(combine_research({"state": "ABOVE_REFERENCE_SUPPORT"},
                                          {"status": "NO_PROFIT_CONTEXT"}))


if __name__ == "__main__":
    unittest.main()
