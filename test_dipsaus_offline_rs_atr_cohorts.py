import unittest
from datetime import date, timedelta
from dipsaus_offline_rs_atr_cohorts import compare_rs_atr_cohorts


def bars(n=310, growth=0.2):
    result = []
    for i in range(n):
        close = 100 + i * growth + (i % 19) * 0.03
        result.append({"date": (date(2024, 1, 1) + timedelta(days=i)).isoformat(),
                       "open": close, "high": close + 1 + (i % 5) * 0.05,
                       "low": close - 1 - (i % 5) * 0.05,
                       "close": close, "volume": 1000})
    return result


class RSATRCohortTests(unittest.TestCase):
    def test_cohorts_are_descriptive_not_trade_ready(self):
        r = compare_rs_atr_cohorts(bars(), bars(growth=0.1), min_per_cohort=5)
        self.assertEqual(r["status"], "EXPLORATORY_POSTHOC_COHORTS")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["cutoffs_pre_registered"])
        self.assertIn("relative_strength", r["comparisons"])
        self.assertIn("atr", r["comparisons"])

    def test_insufficient_sample_blocked(self):
        r = compare_rs_atr_cohorts(bars(n=65), bars(n=65, growth=0.1))
        self.assertEqual(r["status"], "DATA_BLOCKED")
        self.assertEqual(r["reason"], "insufficient_events")

    def test_invalid_minimum_blocked(self):
        r = compare_rs_atr_cohorts(bars(), bars(growth=0.1), min_per_cohort=1)
        self.assertEqual(r["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
