import unittest
from datetime import datetime, timezone
from eu_schedule_gate import scheduled_eu_scan_allowed


def utc(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


class EuropeanScheduleGateTests(unittest.TestCase):
    def test_winter_core_hours(self):
        self.assertFalse(scheduled_eu_scan_allowed("schedule", utc(2026, 11, 10, 7, 59)))
        self.assertTrue(scheduled_eu_scan_allowed("schedule", utc(2026, 11, 10, 8, 0)))
        self.assertTrue(scheduled_eu_scan_allowed("schedule", utc(2026, 11, 10, 16, 29)))
        self.assertFalse(scheduled_eu_scan_allowed("schedule", utc(2026, 11, 10, 16, 30)))

    def test_summer_core_hours(self):
        self.assertFalse(scheduled_eu_scan_allowed("schedule", utc(2026, 7, 10, 6, 59)))
        self.assertTrue(scheduled_eu_scan_allowed("schedule", utc(2026, 7, 10, 7, 0)))
        self.assertTrue(scheduled_eu_scan_allowed("schedule", utc(2026, 7, 10, 15, 29)))
        self.assertFalse(scheduled_eu_scan_allowed("schedule", utc(2026, 7, 10, 15, 30)))

    def test_weekend_and_unknown_event_fail_closed(self):
        self.assertFalse(scheduled_eu_scan_allowed("schedule", utc(2026, 11, 8, 12)))
        self.assertFalse(scheduled_eu_scan_allowed("push", utc(2026, 11, 10, 12)))
        self.assertFalse(scheduled_eu_scan_allowed("schedule", datetime(2026, 11, 10, 12)))

    def test_manual_dispatch_preserved(self):
        self.assertTrue(scheduled_eu_scan_allowed("workflow_dispatch", utc(2026, 11, 8, 12)))


if __name__ == "__main__":
    unittest.main()
