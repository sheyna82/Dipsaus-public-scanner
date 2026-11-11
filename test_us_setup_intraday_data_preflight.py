import unittest
from datetime import datetime, timedelta, timezone
from research.us_setup_intraday_data_preflight import audit_intraday_bars


class IntradayPreflightTests(unittest.TestCase):
    def setUp(self):
        t = datetime(2026, 10, 1, 14, 30, tzinfo=timezone.utc)
        self.rows = [{"timestamp": (t + timedelta(minutes=i)).isoformat(),
                      "low": 99, "close": 100} for i in range(25)]

    def test_minute_bars_accepted_but_not_provider_certified(self):
        result = audit_intraday_bars(self.rows)
        self.assertTrue(result["usable"])
        self.assertFalse(result["provider_verified"])
        self.assertFalse(result["session_calendar_verified"])

    def test_daily_bars_rejected(self):
        rows = [{"timestamp": (datetime(2026, 9, 1, tzinfo=timezone.utc) +
                               timedelta(days=i)).isoformat(), "low": 99, "close": 100}
                for i in range(25)]
        self.assertEqual(audit_intraday_bars(rows)["reason"], "NOT_CONTIGUOUS_INTRADAY")

    def test_date_only_source_rejected(self):
        rows = [{"date": "2026-10-01", "low": 99, "close": 100} for _ in range(25)]
        self.assertEqual(audit_intraday_bars(rows)["reason"], "MISSING_INTRADAY_TIMESTAMP")

    def test_out_of_order_bars_rejected(self):
        rows = list(self.rows)
        rows[5], rows[6] = rows[6], rows[5]
        self.assertEqual(audit_intraday_bars(rows)["reason"], "NON_MONOTONIC_BARS")

    def test_short_series_rejected(self):
        self.assertEqual(audit_intraday_bars(self.rows[:5])["reason"], "INSUFFICIENT_BARS")


if __name__ == "__main__":
    unittest.main()
