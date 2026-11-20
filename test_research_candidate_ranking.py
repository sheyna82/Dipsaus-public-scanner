import unittest
from research_candidate_ranking import rank_research_candidates as rank

BASE = dict(net_profit_eur=180, net_rr=2.5, relative_volume=1.5,
            market_context=0.8, sector_context=0.7)

class ResearchCandidateRankingTests(unittest.TestCase):
    def test_financial_gate_cannot_be_bypassed(self):
        r = rank([{**BASE, "id": "a", "net_profit_eur": 149, "relative_volume": 100}])
        self.assertEqual(r["candidates"][0]["status"], "HARD_FINANCIAL_FILTER_FAILED")
        self.assertIsNone(r["candidates"][0]["quality_score"])

    def test_rr_gate_cannot_be_bypassed(self):
        r = rank([{**BASE, "id": "a", "net_rr": 1.99}])
        self.assertEqual(r["candidates"][0]["status"], "HARD_FINANCIAL_FILTER_FAILED")

    def test_stronger_candidate_ranks_first(self):
        r = rank([{**BASE, "id": "weak"}, {**BASE, "id": "strong",
                  "net_profit_eur": 300, "net_rr": 4, "relative_volume": 2}])
        self.assertEqual(r["candidates"][0]["id"], "strong")
        self.assertLessEqual(r["candidates"][0]["quality_score"], 100)
        self.assertFalse(r["trade_ready"])

    def test_missing_context_does_not_imply_zero(self):
        r = rank([{**BASE, "id": "a", "market_context": None}])
        self.assertEqual(r["candidates"][0]["status"], "UNRANKED_MISSING_OR_INVALID_DATA")

    def test_nonfinite_volume_unranked(self):
        r = rank([{**BASE, "id": "a", "relative_volume": float("inf")}])
        self.assertIsNone(r["candidates"][0]["quality_score"])

    def test_duplicate_ids_block(self):
        r = rank([{**BASE, "id": "a"}, {**BASE, "id": "a"}])
        self.assertEqual(r["status"], "RANKING_INPUT_BLOCKED")

    def test_invalid_market_context_unranked(self):
        r = rank([{**BASE, "id": "a", "market_context": 2}])
        self.assertEqual(r["candidates"][0]["status"], "UNRANKED_INVALID_RANGE")

if __name__ == "__main__":
    unittest.main()
