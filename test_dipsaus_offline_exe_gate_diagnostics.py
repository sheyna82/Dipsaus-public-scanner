import unittest
from dipsaus_offline_exe_gate_diagnostics import explain_no_signal


class GateDiagnosticsTests(unittest.TestCase):
    def test_flat_market_has_no_gates(self):
        bars = [{"open": 100., "high": 100.2, "low": 99.5, "close": 100.}
                for _ in range(35)]
        result = explain_no_signal(bars)
        self.assertEqual(result["evaluated_windows"], 5)
        self.assertEqual(result["all_three_gates"], 0)
        self.assertEqual(result["drawdown_gate"], 0)
        self.assertTrue(result["thresholds_unchanged"])

    def test_decline_counts_same_triggers_as_replay(self):
        bars = [{"open": 100., "high": 100.2, "low": 99.5, "close": 100.}
                for _ in range(30)]
        for i in range(5):
            bars.append({"open": 98.8-i*.2, "high": 99.-i*.2,
                         "low": 98.4-i*.2, "close": 98.5-i*.2})
        self.assertEqual(explain_no_signal(bars)["all_three_gates"], 3)


if __name__ == "__main__":
    unittest.main()
