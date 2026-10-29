"""Offline benchmark excess validation tests. No orders or trading signals."""
import unittest
from candidate_benchmark_excess import compare, market

def rows(n=140,base=100):
    return [{"timestamp":1700000000+i*86400,"open":base*1.03**i,
             "close":base*1.03**i,"low":(base*1.03**i)*.99,
             "high":(base*1.03**i)*1.01,"volume":1000} for i in range(n)]

class BenchmarkExcessTests(unittest.TestCase):
    def test_market_classification(self):
        self.assertEqual(market("AMD"),"US")
        self.assertEqual(market("ASML.AS"),"EU")

    def test_missing_benchmark_alignment_blocks(self):
        stock=rows()
        result=compare(stock,[],"breakout_prior20")
        self.assertEqual(result["status"],"BLOCKED_BENCHMARK_ALIGNMENT")
        self.assertGreater(result["missing_alignment_n"],0)
        self.assertFalse(result["trade_ready"])

    def test_no_signals_never_becomes_positive_result(self):
        flat=rows(base=100)
        for row in flat:
            row.update(open=100,close=100,high=101,low=99)
        result=compare(flat,flat,"breakout_prior20")
        self.assertEqual(result["status"],"NO_SIGNALS")
        self.assertFalse(result["trade_ready"])

if __name__=="__main__":unittest.main()
