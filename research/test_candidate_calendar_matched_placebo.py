import unittest
from candidate_calendar_matched_placebo import calendar_placebo

class CalendarPlaceboTests(unittest.TestCase):
    def setUp(self):
        self.baseline = ([{"session_day": 20000, "excess_pct": float(i)} for i in range(10)] +
                         [{"session_day": 20040, "excess_pct": float(i+10)} for i in range(10)])

    def test_deterministic_and_not_trade_ready(self):
        selected = [self.baseline[0], self.baseline[2], self.baseline[10]]
        a = calendar_placebo(self.baseline, selected, draws=100, seed=4)
        self.assertEqual(a, calendar_placebo(self.baseline, selected, draws=100, seed=4))
        self.assertEqual(a["status"], "DESCRIPTIVE_CALENDAR_MATCHED")
        self.assertEqual(a["calendar_months"], 2)
        self.assertFalse(a["trade_ready"])

    def test_missing_calendar_bucket_blocks(self):
        result = calendar_placebo(self.baseline, [{"session_day": 20100, "excess_pct": 1.0},
                                                  {"session_day": 20101, "excess_pct": 1.0}])
        self.assertEqual(result["status"], "INSUFFICIENT_CALENDAR_MATCHES")

    def test_invalid_day_blocks(self):
        with self.assertRaises(ValueError):
            calendar_placebo(self.baseline, [{"session_day": 1.5, "excess_pct": 1}])

if __name__ == "__main__":
    unittest.main()
