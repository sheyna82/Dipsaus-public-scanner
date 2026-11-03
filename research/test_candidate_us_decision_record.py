"""Offline tests for prospective research decision record builder."""
import unittest
from research.candidate_us_decision_record import decision_record


def assessment(selected=False):
    return {"last_bar_date": "2026-11-02", "drawdown_pct": -10,
            "rebound_from_low_pct": 4, "early_turn": False,
            "established_turn": False, "signal_count": 1,
            "signals": {"positive_2d_change": True},
            "pre_screen_match": selected}


class DecisionRecordTests(unittest.TestCase):
    def test_rejection_captures_reasons_and_hash(self):
        a = decision_record("ABC", assessment(), "2026-11-03T12:00:00Z")
        b = decision_record("ABC", assessment(), "2026-11-03T12:00:00Z")
        self.assertEqual(a, b)
        self.assertIn("DRAWDOWN_BELOW_THRESHOLD", a["rejection_reasons"])
        self.assertIn("TURN_SIGNALS_INSUFFICIENT", a["rejection_reasons"])
        self.assertFalse(a["prospective_capture_independently_verified"])
        self.assertFalse(a["trade_ready"])

    def test_selected_has_no_rejection(self):
        a = assessment(True)
        self.assertEqual(decision_record("ABC", a, "2026-11-03T12:00:00Z")["rejection_reasons"], [])

    def test_future_bar_fails_closed(self):
        a = assessment()
        a["last_bar_date"] = "2026-11-04"
        with self.assertRaisesRegex(ValueError, "FUTURE_BAR_DATE"):
            decision_record("ABC", a, "2026-11-03T12:00:00Z")

    def test_naive_time_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "OBSERVATION_TIME_NOT_UTC"):
            decision_record("ABC", assessment(), "2026-11-03T12:00:00")

    def test_unexplained_rejection_fails_closed(self):
        a = assessment()
        a.update(drawdown_pct=-25, rebound_from_low_pct=4, early_turn=True)
        with self.assertRaisesRegex(ValueError, "UNEXPLAINED_REJECTION"):
            decision_record("ABC", a, "2026-11-03T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
