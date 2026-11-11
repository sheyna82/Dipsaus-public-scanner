import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dipsaus_offline_exe_missing_minutes import audit_regular_session_timestamps


class MissingMinuteTests(unittest.TestCase):
    def test_identifies_missing_minute(self):
        start = datetime(2026, 10, 21, 9, 30, tzinfo=ZoneInfo("America/New_York"))
        stamps = [(start+timedelta(minutes=i)).timestamp() for i in range(390) if i != 17]
        result = audit_regular_session_timestamps(stamps, "2026-10-21")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["missing_count"], 1)
        self.assertIn("09:47:00", result["missing_minutes_ny"][0])
        self.assertEqual(result["synthetic_bars_created"], 0)

    def test_complete_grid(self):
        start = datetime(2026, 10, 21, 9, 30, tzinfo=ZoneInfo("America/New_York"))
        stamps = [(start+timedelta(minutes=i)).timestamp() for i in range(390)]
        self.assertEqual(audit_regular_session_timestamps(stamps, "2026-10-21")["status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
