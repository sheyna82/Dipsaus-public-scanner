"""Offline tests for the minimal Spoor 3 top-three research prototype."""
import unittest
from research_spoor3_top3 import top_three_research_setups as top3

RISK = dict(bid=99.9, ask=100, average_daily_turnover_eur=2_000_000,
            relative_volume=1.5, sessions_until_earnings=12,
            earnings_calendar_checked=True)
BASE = dict(net_profit_eur=180, net_rr=2.5, relative_volume=1.5,
            market_context=0.8, sector_context=0.7)

def candidate(name, **overrides):
    return {**BASE, "id": name, "risk_inputs": dict(RISK), **overrides}

class Spoor3TopThreeTests(unittest.TestCase):
    def test_top_three_order_and_limit(self):
        items = [candidate("weak"), candidate("best", net_profit_eur=350, net_rr=4,
                 relative_volume=2), candidate("mid", net_profit_eur=240),
                 candidate("fourth", net_profit_eur=160)]
        result = top3(items)
        self.assertEqual(result["status"], "TOP3_RESEARCH_ONLY")
        self.assertEqual([x["id"] for x in result["top3"]], ["best", "mid", "weak"])
        self.assertEqual(result["eligible_count"], 4)
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["order_placement_enabled"])

    def test_financial_gate_never_promotes(self):
        result = top3([candidate("low", net_profit_eur=149), candidate("valid")])
        self.assertEqual([x["id"] for x in result["top3"]], ["valid"])
        self.assertEqual(result["excluded"][0]["id"], "low")

    def test_risk_warning_not_in_top_three(self):
        risky = candidate("risky", risk_inputs={**RISK, "average_daily_turnover_eur": 100})
        result = top3([risky, candidate("valid")])
        self.assertEqual([x["id"] for x in result["top3"]], ["valid"])
        self.assertEqual(result["excluded"][0]["research_disposition"], "RISK_WARNING_REVIEW")

    def test_unknown_earnings_excluded(self):
        unknown = candidate("unknown", risk_inputs={**RISK, "earnings_calendar_checked": False})
        result = top3([unknown])
        self.assertEqual(result["top3"], [])
        self.assertEqual(result["eligible_count"], 0)

    def test_invalid_input_fails_closed(self):
        result = top3(None)
        self.assertEqual(result["status"], "TOP3_INPUT_BLOCKED")
        self.assertEqual(result["top3"], [])
        self.assertFalse(result["order_placement_enabled"])

    def test_duplicate_id_fails_closed(self):
        result = top3([candidate("same"), candidate("same")])
        self.assertEqual(result["status"], "TOP3_INPUT_BLOCKED")

if __name__ == "__main__":
    unittest.main()
