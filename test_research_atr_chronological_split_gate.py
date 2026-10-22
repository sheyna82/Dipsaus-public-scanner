import unittest
from datetime import date, timedelta
from research_atr_chronological_split_gate import audit_chronological_split


class ATRChronologicalSplitGateTests(unittest.TestCase):
    def setUp(self):
        first = date(2026, 1, 5)
        self.sessions = [(first + timedelta(days=i)).isoformat() for i in range(80)
                         if (first + timedelta(days=i)).weekday() < 5]

    def audit(self, train_index, holdout_index, **kwargs):
        return audit_chronological_split(
            [{"signal_date": self.sessions[train_index]}],
            [{"signal_date": self.sessions[holdout_index]}],
            self.sessions, **kwargs)

    def test_valid_gap_remains_structural_only(self):
        result = self.audit(4, 15)
        self.assertEqual(result["status"], "STRUCTURAL_REVIEW_ONLY")
        self.assertFalse(result["independent_holdout_verified"])

    def test_embargo_exactly_ten_intervening_sessions(self):
        result = self.audit(4, 14)
        self.assertIn("embargo_not_satisfied", result["errors"])

    def test_reversed_split_rejected(self):
        self.assertIn("chronology_overlap", self.audit(16, 12)["errors"])

    def test_unknown_session_rejected(self):
        result = audit_chronological_split(
            [{"signal_date": "2025-01-01"}],
            [{"signal_date": self.sessions[30]}], self.sessions)
        self.assertIn("signal_outside_calendar", result["errors"])

    def test_duplicate_calendar_rejected(self):
        self.assertIn("unordered_or_duplicate_sessions",
                      audit_chronological_split(
                          [{"signal_date": self.sessions[1]}],
                          [{"signal_date": self.sessions[20]}],
                          self.sessions + [self.sessions[0]])["errors"])


if __name__ == "__main__":
    unittest.main()
