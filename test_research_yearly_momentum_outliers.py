import unittest
from datetime import date, timedelta
from research_yearly_momentum_outliers import yearly_momentum_outlier_sensitivity


class YearlyOutlierTests(unittest.TestCase):
    def test_summary_counts_and_trimmed_mean(self):
        start = date(2025, 1, 1)
        stock = [{"date": (start + timedelta(days=i)).isoformat(),
                  "close": str(100 + i + i % 7)} for i in range(130)]
        spy = [{"date": r["date"], "close": "100"} for r in stock]
        result = yearly_momentum_outlier_sensitivity(stock, spy)
        self.assertFalse(result["trade_ready"])
        for year in result["years"]:
            for side in ("positive", "negative"):
                group = year[side]
                if group["count"] >= 5:
                    self.assertIsNotNone(group["mean_without_extremes_pp"])
                self.assertGreaterEqual(group["count"], 0)

    def test_bad_horizon(self):
        with self.assertRaisesRegex(ValueError, "invalid_horizon"):
            yearly_momentum_outlier_sensitivity([], [], horizon=0)


if __name__ == "__main__":
    unittest.main()
