import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from us_schedule_gate import scheduled_us_scan_allowed

NY = ZoneInfo("America/New_York")


class TestUSScheduleGate(unittest.TestCase):
    def check(self, year, month, day, hour, minute, expected, event="workflow_dispatch"):
        instant = datetime(year, month, day, hour, minute, tzinfo=NY)
        self.assertEqual(scheduled_us_scan_allowed(event, instant), expected)

    def test_winter_boundaries(self):
        for hour, minute, expected in [(9, 29, False), (9, 30, True), (15, 59, True), (16, 0, False)]:
            self.check(2026, 11, 10, hour, minute, expected)

    def test_summer_boundaries(self):
        for hour, minute, expected in [(9, 29, False), (9, 30, True), (15, 59, True), (16, 0, False)]:
            self.check(2026, 7, 10, hour, minute, expected)

    def test_us_eu_dst_mismatch(self):
        self.check(2026, 3, 16, 9, 30, True)
        self.check(2026, 10, 26, 9, 30, True)

    def test_utc_open_boundaries_across_dst(self):
        for year, month, day, open_hour in [
            (2026, 1, 12, 14),
            (2026, 3, 16, 13),
            (2026, 7, 10, 13),
            (2026, 10, 26, 13),
            (2026, 11, 10, 14),
        ]:
            with self.subTest(date=(year, month, day)):
                before = datetime(year, month, day, open_hour, 29, tzinfo=timezone.utc)
                opened = datetime(year, month, day, open_hour, 30, tzinfo=timezone.utc)
                self.assertFalse(scheduled_us_scan_allowed("workflow_dispatch", before))
                self.assertTrue(scheduled_us_scan_allowed("workflow_dispatch", opened))

    def test_weekend(self):
        self.check(2026, 11, 8, 12, 0, False)

    def test_schedule_same_gate(self):
        self.check(2026, 11, 10, 9, 30, True, "schedule")
        self.check(2026, 11, 10, 16, 0, False, "schedule")

    def test_unknown_event(self):
        self.check(2026, 11, 10, 12, 0, False, "push")

    def test_naive_time_fails_closed(self):
        self.assertFalse(scheduled_us_scan_allowed("workflow_dispatch", datetime(2026, 11, 10, 12, 0)))


if __name__ == "__main__":
    unittest.main()
