import unittest
from datetime import date, timedelta
from research_atr_guarded_holdout_evaluation import evaluate_guarded


class GuardedATREvaluationTests(unittest.TestCase):
    def setUp(self):
        start = date(2026, 1, 5)
        self.sessions = [(start + timedelta(days=i)).isoformat() for i in range(90)
                         if (start + timedelta(days=i)).weekday() < 5]

    def event(self, index, severe):
        return {"signal_date": self.sessions[index],
                "structure_above_20d_mean": True, "market_20d_positive": True,
                "atr_expanding": False, "severe": severe}

    def test_valid_chronology_scores_but_never_claims_independence(self):
        result = evaluate_guarded([self.event(0, True), self.event(2, False)],
                                  [self.event(16, True)], self.sessions)
        self.assertEqual(result["status"], "DESCRIPTIVE_ONLY")
        self.assertIn("baseline_brier", result["scores"])
        self.assertFalse(result["trade_ready"])

    def test_overlapping_split_never_scores(self):
        result = evaluate_guarded([self.event(20, True)], [self.event(19, False)],
                                  self.sessions)
        self.assertEqual(result["status"], "DATA_BLOCKED")
        self.assertNotIn("scores", result)

    def test_malformed_outcome_blocks_without_crash(self):
        invalid = self.event(16, True)
        invalid["severe"] = "unknown"
        result = evaluate_guarded([self.event(0, True)], [invalid], self.sessions)
        self.assertEqual(result["status"], "DATA_BLOCKED")
        self.assertEqual(result["reason"], "invalid_scoring_events")
        self.assertNotIn("scores", result)

    def test_insufficient_embargo_never_scores(self):
        result = evaluate_guarded([self.event(10, True)], [self.event(20, False)],
                                  self.sessions)
        self.assertIn("embargo_not_satisfied", result["gate"]["errors"])
        self.assertNotIn("scores", result)


if __name__ == "__main__":
    unittest.main()
