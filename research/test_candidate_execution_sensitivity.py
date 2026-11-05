import unittest
from candidate_execution_sensitivity import execution_sensitivity, compare_liquidity_gates

class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.bars = [{"open": 100.0, "close": 100.0, "volume": 50000}] * 12

    def test_adverse_slippage_reduces_net(self):
        result = execution_sensitivity(self.bars, 0, horizon=10)
        self.assertEqual(result["status"], "DESCRIPTIVE_EXECUTION_SENSITIVITY")
        returns = [x["net_return_pct"] for x in result["scenarios"]]
        self.assertEqual(returns[0], -0.5)
        self.assertEqual(returns, sorted(returns, reverse=True))
        self.assertFalse(result["trade_ready"])

    def test_illiquid_blocks(self):
        bars = [dict(x) for x in self.bars]
        bars[0]["volume"] = 5
        self.assertEqual(execution_sensitivity(bars, 0)["status"], "INSUFFICIENT_ENTRY_LIQUIDITY")

    def test_future_entry_volume_does_not_change_liquidity_decision(self):
        bars = [dict(x) for x in self.bars]
        bars[1]["volume"] = 0
        result = execution_sensitivity(bars, 0)
        self.assertEqual(result["status"], "DESCRIPTIVE_EXECUTION_SENSITIVITY")
        self.assertTrue(result["liquidity_known_before_next_open"])
        self.assertEqual(result["liquidity_observation"], "signal_session_close_times_volume")
        bars[0]["volume"] = 0
        self.assertEqual(execution_sensitivity(bars, 0)["status"], "INSUFFICIENT_ENTRY_LIQUIDITY")

    def test_paired_liquidity_gates_detect_both_disagreement_directions(self):
        bars = [dict(x) for x in self.bars]
        bars[0]["volume"] = 1
        old_only = compare_liquidity_gates(bars, 0)
        self.assertFalse(old_only["signal_gate_pass"])
        self.assertTrue(old_only["legacy_gate_pass"])
        bars[0]["volume"] = 50000
        bars[1]["volume"] = 1
        new_only = compare_liquidity_gates(bars, 0)
        self.assertTrue(new_only["signal_gate_pass"])
        self.assertFalse(new_only["legacy_gate_pass"])
        self.assertTrue(new_only["legacy_is_retrospective"])

    def test_no_future_bars_blocks(self):
        self.assertEqual(execution_sensitivity(self.bars, 10)["status"], "INSUFFICIENT_FUTURE_BARS")

    def test_invalid_slippage_rejected(self):
        with self.assertRaises(ValueError):
            execution_sensitivity(self.bars, 0, adverse_entry_bps=(-1,))

if __name__ == "__main__":
    unittest.main()
