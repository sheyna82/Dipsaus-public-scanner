"""Synthetic regression tests for offline swing P&L research."""
import unittest
from decimal import Decimal
from research_swing_net_pnl import simulate_swing


class SwingNetPnlTests(unittest.TestCase):
    def test_time_exit_profitable_without_costs(self):
        result = simulate_swing(100, [101, 102, 103, 104, 105], 3500, horizon=5)
        self.assertEqual(result["shares"], 35)
        self.assertEqual(result["exit_reason"], "time")
        self.assertEqual(result["net_pnl"], "175.00")
        self.assertEqual(result["exit_session"], 5)

    def test_execution_costs_reduce_profit(self):
        prices = [101, 102, 103, 104, 105]
        baseline = simulate_swing(100, prices, 3500, horizon=5)
        costly = simulate_swing(100, prices, 3500, horizon=5,
                                spread_bps=10, slippage_bps=5, commission_bps=2)
        self.assertLess(Decimal(costly["net_pnl"]), Decimal(baseline["net_pnl"]))

    def test_target_close(self):
        result = simulate_swing(100, [101, 104, 103], 3500,
                                horizon=3, target_pct=3)
        self.assertEqual((result["exit_session"], result["exit_reason"]),
                         (2, "target_close"))

    def test_trailing_close(self):
        result = simulate_swing(100, [103, 106, 102, 108, 109], 3500,
                                horizon=5, trailing_pct=3)
        self.assertEqual((result["exit_session"], result["exit_reason"]),
                         (3, "trailing_close"))

    def test_no_lookahead_after_exit(self):
        a = simulate_swing(100, [105, 95, 80], 3500, horizon=3, target_pct=4)
        b = simulate_swing(100, [105, 200, 300], 3500, horizon=3, target_pct=4)
        self.assertEqual(a["net_pnl"], b["net_pnl"])

    def test_incomplete_or_invalid_data_fail_closed(self):
        for kwargs in ({"horizon": 10}, {"horizon": 2}):
            with self.assertRaises(ValueError):
                simulate_swing(100, [101, 102, 103], 3500, **kwargs)
        for price in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                simulate_swing(price, [101, 102, 103], 3500, horizon=3)

    def test_no_fractional_shares_and_insufficient_capital(self):
        with self.assertRaisesRegex(ValueError, "insufficient_capital"):
            simulate_swing(100, [101, 102, 103], 50, horizon=3)
        result = simulate_swing(100, [101, 102, 103], 350, horizon=3)
        self.assertEqual(result["shares"], 3)


if __name__ == "__main__":
    unittest.main()
