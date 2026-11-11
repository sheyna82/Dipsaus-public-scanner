import unittest
from research_notification_relative_performance import relative_performance

class RelativePerformanceTests(unittest.TestCase):
    def setUp(self):
        self.stock = dict(entry_date="2026-11-02", exit_date="2026-11-06", gross_return_pct=4.5, execution_verified=False)
        self.benchmark = dict(entry_date="2026-11-02", exit_date="2026-11-06", gross_return_pct=1.0, execution_verified=False)

    def test_excess_return(self):
        self.assertEqual(relative_performance(self.stock, self.benchmark)["excess_gross_pct_points"], 3.5)

    def test_missing_benchmark(self):
        self.assertIsNone(relative_performance(self.stock, None))

    def test_reject_misaligned_dates(self):
        with self.assertRaises(ValueError):
            relative_performance(self.stock, dict(self.benchmark, exit_date="2026-11-09"))

    def test_reject_false_execution_claim(self):
        with self.assertRaises(ValueError):
            relative_performance(dict(self.stock, execution_verified=True), self.benchmark)

if __name__ == "__main__":
    unittest.main()
