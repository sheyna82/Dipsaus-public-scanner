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

    def test_next_open_execution_uses_next_bar_not_signal_close(self):
        data = rows()
        data[101]["open"] = 105
        data[101]["high"] = 111
        data[101]["low"] = 104
        data[101]["close"] = 110
        result = model.summarize_next_open(data, [100], 1, 50)
        self.assertEqual(result["status"], "RESEARCH_ONLY")
        self.assertEqual(result["median_net_pct"], 4.26)

    def test_underwater_days_and_severe_drawdown(self):
        data = rows()
        data[101]["open"] = 100
        data[101]["close"] = 95
        data[101]["low"] = 94
        data[102]["close"] = 97
        data[102]["low"] = 85
        result = model.summarize_next_open(data, [100], 2, 50)
        self.assertEqual(result["median_underwater_close_days"], 2)
        self.assertEqual(result["fraction_mae_below_minus_10pct"], 1)
        self.assertEqual(result["fraction_negative_net_at_exit"], 1)

    def test_next_open_missing_blocks(self):
        result = model.summarize_next_open(rows(), [100], 1, 50)
        self.assertEqual(result["status"], "BLOCKED_OPEN_PRICE_MISSING")

    def test_risk_screen_requires_sample_and_controls(self):
        metrics={"status":"RESEARCH_ONLY","n":40,
                 "fraction_mae_below_minus_10pct":0.05,
                 "worst_mae_pct":-8,
                 "fraction_negative_net_at_exit":0.2}
        self.assertEqual(model.risk_screen(metrics,5)["status"],
                         "INSUFFICIENT_MATCHED_CONTROLS")
        metrics["n"]=12
        self.assertEqual(model.risk_screen(metrics,20)["status"],
                         "INSUFFICIENT_INDEPENDENT_SIGNALS")

    def test_risk_screen_rejects_deep_losses_and_never_approves(self):
        metrics={"status":"RESEARCH_ONLY","n":40,
                 "fraction_mae_below_minus_10pct":0.25,
                 "worst_mae_pct":-21,
                 "fraction_negative_net_at_exit":0.2}
        self.assertEqual(model.risk_screen(metrics,20)["status"],"RISK_REJECTED")
        metrics["fraction_mae_below_minus_10pct"]=0.05
        metrics["worst_mae_pct"]=-8
        self.assertEqual(model.risk_screen(metrics,20)["status"],
                         "FURTHER_VALIDATION_REQUIRED")
        self.assertFalse(model.risk_screen(metrics,20)["trade_ready"])

    def test_short_holdout_blocks(self):
        self.assertEqual(model.evaluate(rows(120), 15, "breakout_prior20")["status"],
                         "INSUFFICIENT_TEST_WINDOW")

    def test_nonoverlap_selection(self):
        self.assertEqual(model.nonoverlap([10, 11, 15, 16, 22], 5), [10, 16, 22])


if __name__ == "__main__":
    unittest.main()
