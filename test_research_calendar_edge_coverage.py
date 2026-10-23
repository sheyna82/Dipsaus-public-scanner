import unittest
from research_exchange_session_audit import audit_expected_sessions


class CalendarEdgeCoverageTests(unittest.TestCase):
    def test_missing_first_and_last_calendar_sessions_not_hidden(self):
        report = audit_expected_sessions(
            ["2025-01-03", "2025-01-06"],
            ["2025-01-02", "2025-01-03", "2025-01-06", "2025-01-07"])
        self.assertTrue(report["complete_against_supplied_calendar"])
        self.assertFalse(report["complete_across_full_supplied_calendar"])
        self.assertTrue(report["calendar_coverage_edges_unverified"])
        self.assertEqual(report["calendar_sessions_outside_observed_prices"], 2)

    def test_full_coverage(self):
        report = audit_expected_sessions(
            ["2025-01-02", "2025-01-03"],
            ["2025-01-02", "2025-01-03"])
        self.assertTrue(report["complete_across_full_supplied_calendar"])
        self.assertFalse(report["calendar_coverage_edges_unverified"])


if __name__ == "__main__":
    unittest.main()
