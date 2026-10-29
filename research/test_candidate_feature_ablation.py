"""Offline checks for single-feature ablation safety and cohort accounting."""
import unittest
from candidate_feature_ablation import evaluate_ablation, FILTERS

def rows(n=200, factor=1.03):
    return [{"timestamp":1700000000+i*86400,
             "open":100*factor**i,"close":100*factor**i,
             "high":101*factor**i,"low":99*factor**i,
             "volume":1000+i*5} for i in range(n)]

class AblationTests(unittest.TestCase):
    def test_missing_benchmark_blocks(self):
        result=evaluate_ablation(rows(),[],"breakout_prior20")
        self.assertFalse(result["trade_ready"])
        self.assertNotEqual(result["status"],"DESCRIPTIVE_ONLY")

    def test_flat_prices_no_training_signals(self):
        result=evaluate_ablation(rows(factor=1),rows(factor=1),"breakout_prior20")
        self.assertEqual(result["status"],"INSUFFICIENT_TRAINING_OBSERVATIONS")

    def test_cohort_keys_predeclared(self):
        self.assertEqual(len(FILTERS),5)
        self.assertIn("all_three",FILTERS)
        self.assertIn("baseline",FILTERS)

if __name__=="__main__":unittest.main()
