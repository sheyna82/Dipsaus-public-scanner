"""Synthetic tests for next-session open exit model."""
import unittest
from decimal import Decimal
from research_swing_next_open_execution import simulate_next_open_exit


class NextOpenTests(unittest.TestCase):
    def run_trade(self, **kwargs):
        return simulate_next_open_exit(
            100, [101, 102, 105, 104, 103],
            [100, 101, 98, 103, 101], 3500, **kwargs)

    def test_target_uses_next_open_not_trigger_close(self):
        result = self.run_trade(target_pct=5)
        self.assertEqual(result["exit_decision_session"], 3)
        self.assertEqual(result["exit_reason"], "target_next_open")
        self.assertEqual(Decimal(result["net_pnl"]), Decimal("-70.00"))

    def test_fixed_horizon_uses_following_open(self):
        result = self.run_trade()
        self.assertEqual(result["exit_decision_session"], 5)
        self.assertEqual(Decimal(result["net_pnl"]), Decimal("35.00"))

    def test_gap_can_erase_target_gain(self):
        result = self.run_trade(target_pct=5)
        self.assertLess(Decimal(result["net_pnl"]), 0)

    def test_costs_reduce_net_result(self):
        base = self.run_trade()
        costly = self.run_trade(spread_bps=10, slippage_bps=5,
                                commission_bps=2)
        self.assertLess(Decimal(costly["net_pnl"]), Decimal(base["net_pnl"]))

    def test_missing_following_open_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete_next_open"):
            simulate_next_open_exit(100, [101, 102, 103], [101, 102], 3500,
                                    horizon=3)

    def test_invalid_open_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_price"):
            simulate_next_open_exit(100, [101, 102, 103],
                                    [101, 0, 103], 3500, horizon=3)

    def test_horizon_restricted(self):
        with self.assertRaisesRegex(ValueError, "invalid_horizon"):
            self.run_trade(horizon=4)


if __name__ == "__main__":
    unittest.main()
