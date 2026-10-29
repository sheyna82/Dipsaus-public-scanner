"""Offline invariants for regime-matched candidate controls."""
import importlib.util
import pathlib
import sys
import types
import unittest

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import candidate_regime_cost_validation as model


def rows(n=220):
    return [{"timestamp": i * 86400, "close": 100.0, "high": 101.0,
             "low": 99.0, "volume": 1000} for i in range(n)]


class RegimeCostTests(unittest.TestCase):
    def test_round_trip_cost_is_subtracted_once(self):
        data = rows()
        data[101]["close"] = 110
        self.assertEqual(model.summarize(data, [100], 1, 50)["median_net_pct"], 9.5)

    def test_no_controls_when_pattern_identical_to_regime(self):
        data = rows()
        for i in range(60, 220):
            data[i]["close"] = 100 + i / 10
            data[i]["high"] = data[i]["close"] + 1
            data[i]["low"] = data[i]["close"] - 1
        result = model.evaluate(data, 5, "above_both_mas")
        self.assertEqual(result["matched_control_n"], 0)
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["inferentially_valid"])
        self.assertEqual(result["next_open_execution_status"], "BLOCKED_OPEN_PRICE_MISSING")
        self.assertEqual(result["execution_model"], "SIGNAL_CLOSE_ONLY_UNEXECUTABLE_REFERENCE")

    def test_short_holdout_blocks(self):
        self.assertEqual(model.evaluate(rows(120), 15, "breakout_prior20")["status"],
                         "INSUFFICIENT_TEST_WINDOW")

    def test_nonoverlap_selection(self):
        self.assertEqual(model.nonoverlap([10, 11, 15, 16, 22], 5), [10, 16, 22])


if __name__ == "__main__":
    unittest.main()
