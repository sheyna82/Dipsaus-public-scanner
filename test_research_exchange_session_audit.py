import unittest
from research_exchange_session_audit import audit_expected_sessions


class ExchangeSessionAuditTests(unittest.TestCase):
    def test_weekend_not_flagged_missing(self):
        r = audit_expected_sessions(
            ["2025-01-03", "2025-01-06"],
            ["2025-01-03", "2025-01-06"])
        self.assertEqual(r["missing_expected_sessions"], [])
        self.assertTrue(r["complete_against_supplied_calendar"])
        self.assertFalse(r["calendar_provenance_verified"])

    def test_missing_weekday_session(self):
        r = audit_expected_sessions(
            ["2025-01-02", "2025-01-06"],
            ["2025-01-02", "2025-01-03", "2025-01-06"])
        self.assertEqual(r["missing_expected_sessions"], ["2025-01-03"])

    def test_unexpected_holiday_row(self):
        r = audit_expected_sessions(
            ["2025-01-01", "2025-01-02"],
            ["2024-12-31", "2025-01-02"])
        self.assertEqual(r["unexpected_price_dates"], ["2025-01-01"])

    def test_rejects_calendar_range_gap(self):
        with self.assertRaisesRegex(ValueError, "calendar_range"):
            audit_expected_sessions(
                ["2025-01-02", "2025-01-06"],
                ["2025-01-02", "2025-01-03"])


if __name__ == "__main__":
    unittest.main()
