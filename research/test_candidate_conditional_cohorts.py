"""Deterministic, offline point-in-time cohort checks."""
import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).parent))
from candidate_conditional_cohorts import cohort

class CohortTests(unittest.TestCase):
    def rows(self, n=120):
        return [{"close": 10+i*.02, "high": 10.1+i*.02, "low": 9.9+i*.02, "volume": 1000} for i in range(n)]

    def test_no_future_leakage_into_earlier_entries(self):
        rows = self.rows()
        a = cohort(rows, 10)
        changed = [dict(r) for r in rows]
        changed[-1]["close"] *= 2
        changed[-1]["high"] *= 2
        b = cohort(changed, 10)
        self.assertEqual({k:v['n'] for k,v in a.items()}, {k:v['n'] for k,v in b.items()})

    def test_mae_is_not_positive(self):
        result = cohort(self.rows(), 5)
        self.assertLessEqual(result["all_days"]["median_mae_pct"], 0)
        self.assertGreater(result["all_days"]["n"], 0)

    def test_insufficient_samples_not_eligible(self):
        result = cohort(self.rows(56), 5)
        self.assertFalse(result["all_days"]["eligible"])

if __name__ == "__main__":
    unittest.main()
