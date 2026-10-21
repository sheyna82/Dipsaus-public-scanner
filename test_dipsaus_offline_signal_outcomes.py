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
        for i, row in enumerate(self.rows, 1):
            row["date"] = f"2026-10-{i:02d}"

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

    def test_large_gap_is_flagged_not_silently_filtered(self):
        rows = [dict(x) for x in self.rows]
        rows[1].update(open=150, high=155, low=145, close=152)
        rows[2].update(open=149, high=160, low=140, close=159)
        outcome = evaluate_signal(rows, 0, (1, 2))
        self.assertIsNotNone(outcome)
        self.assertTrue(outcome["large_entry_gap_review"])
        self.assertTrue(outcome["horizons"][1]["large_gap_review"])
        self.assertAlmostEqual(outcome["entry_gap_pct"], 44.2308)
        self.assertFalse(outcome["horizons"][2] is None)

    def test_costs_are_explicit_and_do_not_change_gross_excursion(self):
        gross = evaluate_signal(self.rows, 0, (1,), roundtrip_cost_bps=0)
        net = evaluate_signal(self.rows, 0, (1,), roundtrip_cost_bps=35)
        self.assertEqual(net["roundtrip_cost_bps"], 35)
        self.assertEqual(net["horizons"][1]["close_return_pct"],
                         gross["horizons"][1]["close_return_pct"])
        self.assertAlmostEqual(net["horizons"][1]["estimated_net_close_return_pct"], 1.4682)
        self.assertEqual(net["horizons"][1]["max_favorable_pct"],
                         gross["horizons"][1]["max_favorable_pct"])
        for bad in (-1, True, float("nan"), float("inf"), 10000, "30"):
            self.assertIsNone(evaluate_signal(self.rows, 0, (1,), roundtrip_cost_bps=bad))

    def test_dates_are_required_unique_and_ordered(self):
        bad = [dict(x) for x in self.rows]
        bad[2].pop("date")
        self.assertIsNone(evaluate_signal(bad, 0))
        bad = [dict(x) for x in self.rows]
        bad[2]["date"] = bad[1]["date"]
        self.assertIsNone(evaluate_signal(bad, 0))
        bad = [dict(x) for x in self.rows]
        bad[2]["date"] = "2026-09-30"
        self.assertIsNone(evaluate_signal(bad, 0))
        bad = [dict(x) for x in self.rows]
        bad[2]["date"] = "yesterday"
        self.assertIsNone(evaluate_signal(bad, 0))

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
