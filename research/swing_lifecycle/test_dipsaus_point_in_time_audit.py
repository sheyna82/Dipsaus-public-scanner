import unittest
from dipsaus_point_in_time_audit import audit_rows
BASE=dict(symbol="ABC",decision_at="2026-01-05T20:00:00Z",feature_available_at="2026-01-05T19:00:00Z",entry_at="2026-01-06T14:30:00Z",exit_at="2026-01-12T21:00:00Z",outcome_available_at="2026-01-12T22:00:00Z")
class Tests(unittest.TestCase):
    def issues(self,**updates):
        return [x[1] for x in audit_rows([dict(BASE,**updates)],"2026-01-10T00:00:00Z")]
    def test_training_label(self):self.assertIn("TRAINING_LABEL_NOT_YET_KNOWN",self.issues())
    def test_future_feature(self):self.assertIn("FUTURE_FEATURE",self.issues(feature_available_at="2026-01-05T21:00:00Z"))
    def test_naive_time(self):self.assertIn("INVALID_TIMESTAMP_OR_FIELD",self.issues(decision_at="2026-01-05T20:00:00"))
    def test_entry_before_decision(self):self.assertIn("ENTRY_BEFORE_DECISION",self.issues(entry_at="2026-01-05T19:00:00Z"))
    def test_exit_before_entry(self):self.assertIn("EXIT_BEFORE_ENTRY",self.issues(exit_at="2026-01-06T10:00:00Z"))
    def test_outcome_before_exit(self):self.assertIn("OUTCOME_BEFORE_EXIT",self.issues(outcome_available_at="2026-01-11T21:00:00Z"))
    def test_timezone_equivalence(self):self.assertNotIn("FUTURE_FEATURE",self.issues(feature_available_at="2026-01-05T20:00:00+01:00"))
if __name__=="__main__":unittest.main()
