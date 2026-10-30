import unittest
from research_past_return_signal_baseline import evaluate_past_return_signal


class PastReturnSignalTests(unittest.TestCase):
    def setUp(self):
        self.stock = [{"date": f"2026-10-{d:02d}", "close": str(100+d)} for d in range(1, 12)]
        self.spy = [{"date": f"2026-10-{d:02d}", "close": "100"} for d in range(1, 12)]

    def test_signal_uses_only_past_sessions(self):
        result = evaluate_past_return_signal(self.stock, self.spy, lookback=3, horizon=3)
        self.assertEqual(result["observations"][0]["signal_session"], "2026-10-04")
        self.assertEqual(result["observations"][0]["future_end_session"], "2026-10-07")
        self.assertTrue(result["observations"][0]["signal_positive_past_excess"])
        self.assertFalse(result["predictive_skill_established"])

    def test_rejects_too_few_sessions(self):
        with self.assertRaisesRegex(ValueError, "insufficient"):
            evaluate_past_return_signal(self.stock[:6], self.spy[:6])

    def test_rejects_invalid_windows(self):
        with self.assertRaisesRegex(ValueError, "invalid_windows"):
            evaluate_past_return_signal(self.stock, self.spy, lookback=0)


if __name__ == "__main__":
    unittest.main()
