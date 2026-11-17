"""Offline timezone/session checks, synthetic dates only."""
import unittest
from research.us_session_clock_20261117 import classify_regular_session

class SessionClockTests(unittest.TestCase):
    def check(self, stamps, timeframe="hourly"):
        return classify_regular_session([{"time": t} for t in stamps], timeframe=timeframe)
    def test_winter_regular_open(self):
        r = self.check(["2026-11-17T14:30:00Z"])
        self.assertEqual(r["status"], "CLOCK_SCREENED_UNVERIFIED")
        self.assertFalse(r["exchange_calendar_verified"])
        self.assertFalse(r["trade_ready"])
    def test_summer_regular_open(self):
        self.assertEqual(self.check(["2026-07-15T13:30:00Z"])["status"], "CLOCK_SCREENED_UNVERIFIED")
    def test_winter_before_open(self):
        self.assertIn("OUTSIDE_REGULAR_SESSION", self.check(["2026-11-17T14:29:00Z"])["blocks"])
    def test_summer_after_close(self):
        self.assertIn("OUTSIDE_REGULAR_SESSION", self.check(["2026-07-15T20:00:00Z"])["blocks"])
    def test_weekend(self):
        self.assertIn("WEEKEND_BAR", self.check(["2026-11-14T15:00:00Z"])["blocks"])
    def test_naive_timestamp(self):
        self.assertIn("BAR_TIME_NOT_AWARE", self.check(["2026-11-17T14:30:00"])["blocks"])
    def test_daily_not_intraday_clock_checked(self):
        r = self.check(["2026-11-17T00:00:00Z"], timeframe="daily")
        self.assertEqual(r["status"], "CLOCK_SCREENED_UNVERIFIED")
    def test_unknown_timeframe(self):
        self.assertIn("TIMEFRAME_UNSUPPORTED", self.check(["2026-11-17T14:30:00Z"], "minute")["blocks"])

if __name__ == "__main__":
    unittest.main()
