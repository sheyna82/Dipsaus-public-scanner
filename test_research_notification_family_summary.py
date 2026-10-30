import unittest
from research_notification_family_summary import summarize_families
class SummaryTests(unittest.TestCase):
    def test_no_profitability_ranking(self):
        stages=[{"symbol":"EXE","stage":"MOMENTUM_NEAR_HIGH"},{"symbol":"VIST","stage":"MOMENTUM_NEAR_HIGH"}]
        m=[{"symbol":s,"horizons":{h:{"ready":False} for h in ("3","5","10","20")}} for s in ("EXE","VIST")]
        r=summarize_families(stages,m)
        self.assertEqual(r["families"]["MOMENTUM_NEAR_HIGH"]["cases"],2)
        self.assertFalse(r["profitability_ranking_available"])
    def test_missing_maturity_is_error(self):
        with self.assertRaises(ValueError):
            summarize_families([{"symbol":"EXE","stage":"MOMENTUM_NEAR_HIGH"}],[])
if __name__=="__main__":unittest.main()
