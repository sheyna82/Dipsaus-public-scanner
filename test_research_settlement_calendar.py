import unittest
from datetime import date, datetime
from research_settlement_calendar import settlement_business_date as settle

class SettlementCalendarTests(unittest.TestCase):
    def test_friday_two_business_days_reaches_tuesday(self):
        result = settle(date(2026, 11, 6), lag_business_days=2)
        self.assertEqual(result["settlement_date"], "2026-11-10")
        self.assertFalse(result["broker_rule_verified"])

    def test_explicit_holiday_skipped(self):
        result = settle(date(2026, 11, 6), lag_business_days=2,
                        holidays=(date(2026, 11, 9),))
        self.assertEqual(result["settlement_date"], "2026-11-11")
        self.assertFalse(result["holiday_calendar_coverage_verified"])

    def test_zero_lag_same_business_day(self):
        self.assertEqual(settle(date(2026, 11, 5), lag_business_days=0)["settlement_date"],
                         "2026-11-05")

    def test_weekend_exit_rejected(self):
        with self.assertRaisesRegex(ValueError, "EXIT_NOT_BUSINESS_DAY"):
            settle(date(2026, 11, 7), lag_business_days=2)

    def test_invalid_lag_and_holidays_rejected(self):
        for lag in (True, -1, 1.5):
            with self.subTest(lag=lag):
                with self.assertRaisesRegex(ValueError, "INVALID_BUSINESS_DAY_LAG"):
                    settle(date(2026, 11, 5), lag_business_days=lag)
        with self.assertRaisesRegex(ValueError, "INVALID_HOLIDAY_CALENDAR"):
            settle(date(2026, 11, 5), lag_business_days=2, holidays=["2026-11-06"])

    def test_datetime_not_accepted_as_date(self):
        with self.assertRaisesRegex(ValueError, "INVALID_EXIT_DATE"):
            settle(datetime(2026, 11, 5), lag_business_days=2)

if __name__ == "__main__":
    unittest.main()
