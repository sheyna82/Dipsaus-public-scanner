"""Offline tests: no network, broker, or notifications."""
import unittest
from dipsaus_offline_signal_outcomes import evaluate_signal


class OutcomeTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"open": 100, "high": 105, "low": 98, "close": 104},
            {"open": 110, "high": 115, "low": 105, "close": 112},
            {"open": 108, "high": 120, "low": 99, "close": 119},
            {"open": 118, "high": 125, "low": 113, "close": 123},
        ]

    def test_next_open_avoids_same_day_lookahead(self):
        outcome = evaluate_signal(self.rows, 0, (1, 2, 3))
        self.assertEqual(outcome["entry_open"], 110)
        self.assertAlmostEqual(outcome["horizons"][1]["close_return_pct"], 1.8182)
        self.assertAlmostEqual(outcome["horizons"][2]["max_favorable_pct"], 9.0909)
        self.assertEqual(outcome["horizons"][2]["max_adverse_pct"], -10.0)

    def test_incomplete_horizon_is_explicitly_missing(self):
        outcome = evaluate_signal(self.rows, 2, (1, 3, 5))
        self.assertIsNotNone(outcome["horizons"][1])
        self.assertIsNone(outcome["horizons"][3])
        self.assertIsNone(outcome["horizons"][5])

    def test_invalid_data_fails_closed(self):
        self.assertIsNone(evaluate_signal(self.rows, 3))
        self.assertIsNone(evaluate_signal(self.rows, -1))
        self.assertIsNone(evaluate_signal(self.rows, True))
        self.assertIsNone(evaluate_signal(self.rows, 0, (0,)))
        bad = [dict(x) for x in self.rows]
        bad[2]["low"] = float("nan")
        self.assertIsNone(evaluate_signal(bad, 0))
        bad = [dict(x) for x in self.rows]
        bad[2]["high"] = 100
        self.assertIsNone(evaluate_signal(bad, 0))


if __name__ == "__main__":
    unittest.main()
