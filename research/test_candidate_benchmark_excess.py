"""Offline checks for benchmark-relative historical comparison."""
import unittest
from candidate_benchmark_excess import compare, market

def rows(n=140,open_price=100,close_price=100,step=86400):
    return [{"timestamp":1700000000+i*step,"open":open_price,"close":close_price,
             "low":close_price*.99,"high":close_price*1.01,"volume":1000}
            for i in range(n)]

class BenchmarkExcessTests(unittest.TestCase):
    def test_market_classification(self):
        self.assertEqual(market("AMD"),"US")
        self.assertEqual(market("ASML.AS"),"EU")

    def test_missing_benchmark_alignment_blocks(self):
        stock=rows()
        for i in range(20,len(stock)):
            stock[i]["close"]=101+i*.3
            stock[i]["high"]=stock[i]["close"]*1.01
            stock[i]["low"]=stock[i]["close"]*.99
        result=compare(stock,[], "breakout_prior20")
        self.assertEqual(result["status"],"BLOCKED_BENCHMARK_ALIGNMENT")
        self.assertGreater(result["missing_alignment_n"],0)
        self.assertFalse(result["trade_ready"])

    def test_no_signals_never_becomes_positive_result(self):
        result=compare(rows(),rows(),"breakout_prior20")
        self.assertEqual(result["status"],"NO_SIGNALS")
        self.assertFalse(result["trade_ready"])

if __name__=="__main__":unittest.main()
