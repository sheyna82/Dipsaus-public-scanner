import unittest
from datetime import datetime, timezone
from dipsaus_offline_completed_daily_bar_gate import completed_daily_bars


class CompletedDailyBarGateTests(unittest.TestCase):
    def test_today_bar_is_removed_before_market_close(self):
        rows = [{"date": "2026-10-21"}, {"date": "2026-10-22"}]
        result = completed_daily_bars(rows, now_utc=datetime(2026, 10, 22, 14, 30, tzinfo=timezone.utc))
        self.assertEqual(result["status"], "PRIOR_DATE_ONLY")
        self.assertEqual(result["latest_completed_date"], "2026-10-21")
        self.assertEqual(result["discarded_unconfirmed_bars"], 1)

    def test_today_bar_removed_even_after_close(self):
        rows = [{"date": "2026-10-21"}, {"date": "2026-10-22"}]
        result = completed_daily_bars(rows, now_utc=datetime(2026, 10, 23, 1, tzinfo=timezone.utc))
        self.assertEqual(result["latest_completed_date"], "2026-10-21")

    def test_naive_clock_blocks(self):
        self.assertEqual(completed_daily_bars([{"date": "2026-10-21"}],
                    now_utc=datetime(2026, 10, 22))["status"], "DATA_BLOCKED")

    def test_only_today_blocks(self):
        self.assertEqual(completed_daily_bars([{"date": "2026-10-22"}],
                    now_utc=datetime(2026, 10, 22, 16, tzinfo=timezone.utc))["status"],
                    "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
