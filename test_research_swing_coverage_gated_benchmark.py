import unittest
from research_swing_coverage_gated_benchmark import compare_with_historical_coverage

def bars(days):
    return [{"date": "2026-01-%02d" % day} for day in days]

class CoverageGatedBenchmarkTests(unittest.TestCase):
    def test_missing_benchmark_blocks_before_portfolio(self):
        r = compare_with_historical_coverage(["AAA"], ["SPY"],
            {"AAA": bars([1,2,3])}, [], 21000, min_sessions=2)
        self.assertTrue(r["comparison_blocked"])
        self.assertIsNone(r["comparison"])
    def test_disjoint_histories_block(self):
        r = compare_with_historical_coverage(["AAA"], ["SPY"],
            {"AAA": bars([1,2,3]), "SPY": bars([4,5,6])}, [], 21000, min_sessions=2)
        self.assertTrue(r["comparison_blocked"])
    def test_full_coverage_refuses_mismatched_candidates(self):
        with self.assertRaises(ValueError):
            compare_with_historical_coverage(["AAA"], ["SPY"],
                {"AAA": bars([1,2,3]), "SPY": bars([1,2,3])},
                [], 21000, min_sessions=2)
if __name__ == "__main__":
    unittest.main()
