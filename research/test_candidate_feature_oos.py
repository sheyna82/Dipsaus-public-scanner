"""Offline safety tests for out-of-sample feature filtering."""
import unittest
from candidate_feature_oos import evaluate_filtered

def rows(n=180,trend=1.01):
    return [{"timestamp":1700000000+i*86400,"open":100*trend**i,
             "close":100*trend**i,"high":101*trend**i,
             "low":99*trend**i,"volume":1000+i*10} for i in range(n)]

class OOSTests(unittest.TestCase):
    def test_missing_benchmark_never_approves_trade(self):
        result=evaluate_filtered(rows(),[],"breakout_prior20")
        self.assertFalse(result["trade_ready"])
        self.assertIn(result["status"],("INSUFFICIENT_VALID_FEATURES",
                                       "INSUFFICIENT_TRAINING_OBSERVATIONS"))

    def test_flat_market_has_no_positive_filtered_claim(self):
        stock=rows(trend=1)
        result=evaluate_filtered(stock,stock,"breakout_prior20")
        self.assertFalse(result["trade_ready"])
        self.assertEqual(result["status"],"INSUFFICIENT_TRAINING_OBSERVATIONS")

if __name__=="__main__":unittest.main()
