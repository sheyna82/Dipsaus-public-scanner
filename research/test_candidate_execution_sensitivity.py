import unittest
from candidate_execution_sensitivity import execution_sensitivity

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
        bars[1]["volume"] = 5
        self.assertEqual(execution_sensitivity(bars, 0)["status"], "INSUFFICIENT_ENTRY_LIQUIDITY")

    def test_no_future_bars_blocks(self):
        self.assertEqual(execution_sensitivity(self.bars, 10)["status"], "INSUFFICIENT_FUTURE_BARS")

    def test_invalid_slippage_rejected(self):
        with self.assertRaises(ValueError):
            execution_sensitivity(self.bars, 0, adverse_entry_bps=(-1,))

if __name__ == "__main__":
    unittest.main()
