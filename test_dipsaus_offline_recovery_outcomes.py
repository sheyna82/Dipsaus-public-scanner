import unittest
from dipsaus_offline_recovery_outcomes import evaluate_recovery_path


def bar(day, high, low, close):
    return {"date": day, "high": high, "low": low, "close": close}


class RecoveryOutcomeTests(unittest.TestCase):
    def test_gain_first(self):
        b = [bar("2026-10-01", 101, 99, 100),
             bar("2026-10-02", 104, 99, 103),
             bar("2026-10-05", 106, 102, 105)]
        r = evaluate_recovery_path(b, horizon=2)
        self.assertEqual(r["status"], "GAIN_FIRST")
        self.assertEqual(r["touch_session"], 1)
        self.assertEqual(r["close_return_pct"], 5)

    def test_loss_first(self):
        b = [bar("2026-10-01", 101, 99, 100),
             bar("2026-10-02", 100, 94, 96)]
        self.assertEqual(evaluate_recovery_path(b, horizon=1)["status"], "LOSS_FIRST")

    def test_same_bar_is_ambiguous_not_winner(self):
        b = [bar("2026-10-01", 101, 99, 100),
             bar("2026-10-02", 105, 94, 99)]
        self.assertEqual(evaluate_recovery_path(b, horizon=1)["status"],
                         "AMBIGUOUS_SAME_BAR")

    def test_timeout_and_insufficient(self):
        b = [bar("2026-10-01", 101, 99, 100),
             bar("2026-10-02", 102, 98, 101)]
        self.assertEqual(evaluate_recovery_path(b, horizon=1)["status"], "TIMEOUT")
        self.assertEqual(evaluate_recovery_path(b, horizon=2)["status"],
                         "INSUFFICIENT_FUTURE_DATA")

    def test_invalid_bar_and_dates(self):
        b = [bar("2026-10-02", 101, 99, 100),
             bar("2026-10-01", 105, 94, 99)]
        self.assertIsNone(evaluate_recovery_path(b, horizon=1))
        self.assertIsNone(evaluate_recovery_path(
            [bar("2026-10-01", 98, 99, 100)], horizon=1))


if __name__ == "__main__":
    unittest.main()
