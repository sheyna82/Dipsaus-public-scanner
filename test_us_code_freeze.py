"""Deterministic DST and weekday checks for US research code freeze."""
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from us_code_freeze import code_freeze_active

NY = ZoneInfo("America/New_York")


class CodeFreezeTests(unittest.TestCase):
    def at_ny(self, year, month, day, hour, minute):
        return datetime(year, month, day, hour, minute, tzinfo=NY)

    def test_november_start(self):
        self.assertFalse(code_freeze_active(self.at_ny(2026, 11, 19, 9, 24)))
        self.assertTrue(code_freeze_active(self.at_ny(2026, 11, 19, 9, 25)))

    def test_november_close(self):
        self.assertTrue(code_freeze_active(self.at_ny(2026, 11, 19, 15, 59)))
        self.assertFalse(code_freeze_active(self.at_ny(2026, 11, 19, 16, 0)))

    def test_march_dst_gap_netherlands(self):
        # US daylight saving starts before Europe's: 09:25 NY = 14:25 NL.
        ny = self.at_ny(2027, 3, 15, 9, 25)
        nl = ny.astimezone(ZoneInfo("Europe/Amsterdam"))
        self.assertEqual((nl.hour, nl.minute), (14, 25))
        self.assertTrue(code_freeze_active(ny))

    def test_winter_netherlands(self):
        ny = self.at_ny(2026, 11, 19, 9, 25)
        nl = ny.astimezone(ZoneInfo("Europe/Amsterdam"))
        self.assertEqual((nl.hour, nl.minute), (15, 25))

    def test_weekend_not_frozen(self):
        self.assertFalse(code_freeze_active(self.at_ny(2026, 11, 21, 12, 0)))

    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            code_freeze_active(datetime(2026, 11, 19, 9, 25))

    def test_utc_equivalence(self):
        ny = self.at_ny(2026, 11, 19, 10, 0)
        self.assertEqual(code_freeze_active(ny),
                         code_freeze_active(ny.astimezone(timezone.utc)))


    def test_midday_frozen_on_weekday(self):
        # The same pure predicate is used by the fail-closed CLI.
        self.assertTrue(code_freeze_active(self.at_ny(2026, 11, 19, 9, 25)))

    def test_dst_end_transition_gap_netherlands(self):
        # Europe returns to winter time before US: 09:25 NY = 14:25 NL.
        ny = self.at_ny(2027, 11, 1, 9, 25)
        nl = ny.astimezone(ZoneInfo("Europe/Amsterdam"))
        self.assertEqual((nl.hour, nl.minute), (14, 25))
        self.assertTrue(code_freeze_active(ny))


if __name__ == "__main__":
    unittest.main()
