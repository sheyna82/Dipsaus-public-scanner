import unittest
from research_swing_intratrade_excursion import excursion_for_trade,summarize_excursions

class ExcursionTests(unittest.TestCase):
    def test_known_extremes(self):
        bars=[{"open":100,"high":101,"low":99,"close":100} for _ in range(20)]
        bars[1]={"open":100,"high":105,"low":92,"close":103}
        bars[2]={"open":103,"high":110,"low":99,"close":108}
        bars[5]={"open":108,"high":109,"low":101,"close":105}
        r=excursion_for_trade(bars,0,5,entry_cost_bps=30)
        self.assertEqual(r["mae_pct"],-8.0)
        self.assertEqual(r["mfe_pct"],10.0)
        self.assertEqual(r["exit_net_pct"],4.7)
        self.assertEqual(summarize_excursions([r])["worst_mae_pct"],-8.0)
    def test_rejects_missing_future(self):
        bars=[{"open":100,"high":101,"low":99,"close":100} for _ in range(5)]
        with self.assertRaises(ValueError):
            excursion_for_trade(bars,0,5)
if __name__=="__main__":
    unittest.main()
