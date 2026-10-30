import unittest
from research_swing_user_event_examples import EXAMPLES, summarize_examples

class UserEventExamplesTests(unittest.TestCase):
    def test_all_six_symbols_preserved(self):
        self.assertEqual({e["symbol"] for e in EXAMPLES},
                         {"AMD", "AMZN", "PLTR", "COHU", "MC.PA", "VIE.PA"})

    def test_duplicate_cohu_event_is_not_independent(self):
        summary = summarize_examples()
        self.assertEqual(summary["event_alert_count"], 5)
        self.assertEqual(summary["distinct_event_count"], 4)
        self.assertEqual(summary["duplicate_event_alert_count"], 1)

    def test_recovery_examples_stay_separate(self):
        self.assertEqual(summarize_examples()["recovery_watch_count"], 2)

    def test_no_unverified_case_is_trade_ready(self):
        self.assertFalse(summarize_examples()["trade_ready"])
        self.assertTrue(all(e["status"] == "unverified" for e in EXAMPLES))

if __name__ == "__main__":
    unittest.main()
