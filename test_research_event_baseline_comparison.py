"""Synthetic offline benchmark comparison tests."""
import unittest
from research_event_baseline_comparison import compare_event_to_benchmark


def series(values, dates=None):
    dates = dates or [f"2026-10-{day:02d}" for day in range(19, 25)]
    return [{"date": date, "close": value} for date, value in zip(dates, values)]


class BaselineComparisonTests(unittest.TestCase):
    def test_excess_return_is_not_predictive_skill(self):
        result = compare_event_to_benchmark(
            series([100, 110, 105, 120, 118, 125]),
            series([100, 102, 103, 104, 105, 106]))
        self.assertEqual([x["sessions_after_baseline"] for x in result["horizons"]],
                         [1, 3, 5])
        self.assertEqual(result["horizons"][0]["excess_return_percentage_points"], "8.00")
        self.assertFalse(result["predictive_skill_established"])
        self.assertFalse(result["trade_ready"])

    def test_reject_mismatched_dates(self):
        with self.assertRaisesRegex(ValueError, "stock_benchmark_dates_mismatch"):
            compare_event_to_benchmark(
                series([100] * 6),
                series([100] * 6, dates=[f"2026-11-{day:02d}" for day in range(1, 7)]))

    def test_reject_missing_and_invalid_prices(self):
        with self.assertRaisesRegex(ValueError, "insufficient_aligned_sessions"):
            compare_event_to_benchmark(series([100, 101]), series([100, 101]))
        with self.assertRaisesRegex(ValueError, "invalid_session_price"):
            compare_event_to_benchmark(series([100, 100, 100, 0, 100, 100]),
                                       series([100] * 6))


if __name__ == "__main__":
    unittest.main()
