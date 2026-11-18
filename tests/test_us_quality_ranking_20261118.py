import unittest
from research.us_quality_ranking_20261118 import (
    WEIGHTS, rank_quality_components, order_research_queue)

def complete(value=1.0):
    return {k: {"verified_asof": True, "fraction": value} for k in WEIGHTS}

class QualityRankingTests(unittest.TestCase):
    def test_perfect(self):
        self.assertEqual(rank_quality_components(complete())["score_0_100"], 100)
    def test_zero(self):
        self.assertEqual(rank_quality_components(complete(0))["score_0_100"], 0)
    def test_half(self):
        self.assertEqual(rank_quality_components(complete(.5))["score_0_100"], 50)
    def test_missing_unranked(self):
        c=complete();del c["news_events"]
        x=rank_quality_components(c)
        self.assertIsNone(x["score_0_100"])
        self.assertEqual(x["observed_points"],90)
    def test_missing_not_zero(self):
        c=complete(0);del c["news_events"]
        self.assertIsNone(rank_quality_components(c)["score_0_100"])
    def test_bool_invalid(self):
        c=complete();c["news_events"]["fraction"]=True
        self.assertEqual(rank_quality_components(c)["status"],"INVALID_COMPONENTS")
    def test_unverified_invalid(self):
        c=complete();c["news_events"]["verified_asof"]=False
        self.assertEqual(rank_quality_components(c)["status"],"INVALID_COMPONENTS")
    def test_out_of_range_invalid(self):
        c=complete();c["news_events"]["fraction"]=1.1
        self.assertEqual(rank_quality_components(c)["status"],"INVALID_COMPONENTS")
    def test_nan_invalid(self):
        c=complete();c["news_events"]["fraction"]=float("nan")
        self.assertEqual(rank_quality_components(c)["status"],"INVALID_COMPONENTS")
    def test_unknown_key_invalid(self):
        c=complete();c["extra"]=None
        self.assertEqual(rank_quality_components(c)["status"],"INVALID_COMPONENTS")
    def test_no_evidence(self):
        self.assertEqual(len(rank_quality_components({})["unknown"]),5)
    def test_invalid_root(self):
        self.assertEqual(rank_quality_components(None)["status"],"INVALID_COMPONENTS")
    def test_rank_complete_first(self):
        c=complete();partial=complete();del partial["news_events"]
        x=order_research_queue([{"symbol":"A","quality_components":partial},
                                {"symbol":"B","quality_components":c}])
        self.assertEqual([r["symbol"] for r in x["rows"]],["B","A"])
    def test_rank_descending(self):
        x=order_research_queue([{"symbol":"A","quality_components":complete(.2)},
                                {"symbol":"B","quality_components":complete(.8)}])
        self.assertEqual(x["rows"][0]["symbol"],"B")
    def test_keep_all(self):
        x=order_research_queue([{"symbol":"A"},{"symbol":"B"}])
        self.assertEqual(len(x["rows"]),2)
    def test_stable_ties(self):
        x=order_research_queue([{"symbol":"B","quality_components":complete()},
                                {"symbol":"A","quality_components":complete()}])
        self.assertEqual([r["symbol"] for r in x["rows"]],["B","A"])
    def test_invalid_candidate(self):
        with self.assertRaises(ValueError):
            order_research_queue([{}])
    def test_execution_stays_blocked(self):
        x=rank_quality_components(complete())
        self.assertFalse(x["trade_ready"])
        self.assertFalse(x["notify"])
        self.assertFalse(x["automatic_orders"])
        self.assertFalse(x["order_placement_enabled"])

if __name__=="__main__":
    unittest.main()
