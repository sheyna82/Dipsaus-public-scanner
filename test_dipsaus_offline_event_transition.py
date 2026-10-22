import unittest
from dipsaus_offline_event_transition import evaluate_transition


def state(classification, **changes):
    value = {"status": "RESEARCH_ONLY", "symbol": "TSLA",
             "event_id": "2026-q3", "classification": classification}
    value.update(changes)
    return value


class EventTransitionTests(unittest.TestCase):
    def test_unchanged_suppressed(self):
        self.assertEqual(evaluate_transition(state("REVIEW_ENTRY"),
                                             state("REVIEW_ENTRY"))["status"],
                         "SUPPRESSED")

    def test_wait_transition_suppressed(self):
        self.assertEqual(evaluate_transition(state("REVIEW_ENTRY"),
                                             state("WAIT_CONFIRMATION"))["status"],
                         "SUPPRESSED")

    def test_new_risk_review_candidate(self):
        result = evaluate_transition(state("WAIT_CONFIRMATION"),
                                     state("RISK_ELEVATED"))
        self.assertEqual(result["status"], "REVIEW_CANDIDATE")
        self.assertFalse(result["notification_sent"])

    def test_new_entry_review_candidate(self):
        self.assertEqual(evaluate_transition(state("WAIT_CONFIRMATION"),
                                             state("REVIEW_ENTRY"))["status"],
                         "REVIEW_CANDIDATE")

    def test_no_baseline_suppressed(self):
        self.assertEqual(evaluate_transition(None, state("REVIEW_ENTRY"))["status"],
                         "SUPPRESSED")

    def test_different_event_suppressed(self):
        self.assertEqual(evaluate_transition(state("WAIT_CONFIRMATION"),
                                             state("REVIEW_ENTRY", event_id="2026-q4"))["status"],
                         "SUPPRESSED")

    def test_blocked_current_suppressed(self):
        self.assertEqual(evaluate_transition(state("WAIT_CONFIRMATION"),
                                             {"status": "DATA_BLOCKED"})["status"],
                         "SUPPRESSED")


if __name__ == "__main__":
    unittest.main()
