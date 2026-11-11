"""Offline regression tests for exact-date benchmark matching."""
import unittest
from research_earnings_benchmark_comparison import compare

class BenchmarkComparisonTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{"symbol":"TEST","event_date":"2026-06-01","entry_date":"2026-06-02","exit_date":"2026-06-04","horizon":3,"gross_return_pct":5.0}]
        self.bars=[{"date":"2026-06-02","open":100,"close":101},{"date":"2026-06-04","open":103,"close":102}]

    def test_excess_and_cost_cancellation(self):
        result=compare(self.rows,self.bars,20)
        self.assertEqual(result["cohorts"][0]["matched_n"],1)
        self.assertAlmostEqual(result["cohorts"][0]["mean_excess_pct"],3.0)
        self.assertFalse(result["trade_ready"])

    def test_missing_exact_date_is_rejected_not_substituted(self):
        with self.assertRaisesRegex(ValueError,"no_exact_date_matches"):
            compare(self.rows,self.bars[:1])

    def test_duplicate_events_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"duplicate_event_horizon"):
            compare(self.rows*2,self.bars)

    def test_duplicate_benchmark_date_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"duplicate_benchmark_date"):
            compare(self.rows,self.bars+self.bars[:1])

if __name__=="__main__": unittest.main()
