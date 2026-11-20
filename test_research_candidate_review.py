import unittest
from research_candidate_review import review_research_candidates as review

BASE = dict(net_profit_eur=200, net_rr=3, relative_volume=1.5,
            market_context=0.8, sector_context=0.8)
RISK = dict(bid=99.9, ask=100, average_daily_turnover_eur=2_000_000,
            relative_volume=1.5, earnings_calendar_checked=True,
            sessions_until_earnings=9)

def candidate(id, **changes):
    return {**BASE, "id": id, "risk_inputs": dict(RISK), **changes}

class ResearchCandidateReviewTests(unittest.TestCase):
    def test_clean_candidate_is_still_research_only(self):
        r = review([candidate("a")])
        x = r["candidates"][0]
        self.assertEqual(x["research_disposition"], "RESEARCH_REVIEW_CANDIDATE")
        self.assertTrue(x["eligible_for_further_research"])
        self.assertFalse(x["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])

    def test_high_score_does_not_override_earnings(self):
        r = review([candidate("a", net_profit_eur=500, net_rr=5,
                   risk_inputs={**RISK, "sessions_until_earnings": 2})])
        x = r["candidates"][0]
        self.assertEqual(x["research_disposition"], "RISK_WARNING_REVIEW")
        self.assertFalse(x["eligible_for_further_research"])

    def test_high_score_does_not_override_liquidity(self):
        r = review([candidate("a", risk_inputs={**RISK, "bid": 95})])
        self.assertEqual(r["candidates"][0]["research_disposition"], "RISK_WARNING_REVIEW")

    def test_unknown_earnings_is_not_safe(self):
        r = review([candidate("a", risk_inputs={**RISK, "earnings_calendar_checked": False})])
        self.assertEqual(r["candidates"][0]["research_disposition"], "EARNINGS_UNKNOWN_REVIEW")

    def test_financial_gate_wins_over_high_risk_score(self):
        r = review([candidate("a", net_profit_eur=149)])
        self.assertEqual(r["candidates"][0]["research_disposition"],
                         "NOT_RANKABLE_OR_FINANCIAL_GATE_FAILED")

    def test_invalid_risk_inputs_do_not_pass(self):
        r = review([candidate("a", risk_inputs={**RISK, "ask": None})])
        self.assertEqual(r["candidates"][0]["research_disposition"], "RISK_DATA_BLOCKED")

    def test_missing_risk_inputs_blocks_batch(self):
        r = review([{**BASE, "id": "a"}])
        self.assertEqual(r["status"], "REVIEW_INPUT_BLOCKED")

    def test_duplicate_ids_block_batch(self):
        r = review([candidate("a"), candidate("a")])
        self.assertEqual(r["status"], "REVIEW_INPUT_BLOCKED")

if __name__ == "__main__":
    unittest.main()
