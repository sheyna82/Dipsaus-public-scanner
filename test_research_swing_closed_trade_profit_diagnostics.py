import unittest
from research_swing_closed_trade_profit_diagnostics import analyze_closed_trade_pnl


class ClosedTradeDiagnosticsTests(unittest.TestCase):
    def test_mixed_net_trades(self):
        result = analyze_closed_trade_pnl([100, -50, 200, -25])
        self.assertEqual(result["net_profit"], "225.00")
        self.assertEqual(result["average_net_pnl_per_trade"], "56.25")
        self.assertEqual(result["profit_factor"], "4.0000")
        self.assertEqual(result["win_rate_pct"], "50.00")

    def test_all_winners_no_infinite_claim(self):
        result = analyze_closed_trade_pnl([20, 10])
        self.assertEqual(result["profit_factor"], "undefined_no_losses")
        self.assertIsNone(result["average_loss"])

    def test_all_losers(self):
        result = analyze_closed_trade_pnl([-10, -20])
        self.assertEqual(result["profit_factor"], "0.0000")
        self.assertEqual(result["net_profit"], "-30.00")

    def test_breakeven(self):
        result = analyze_closed_trade_pnl([0, 0])
        self.assertEqual(result["profit_factor"], "undefined_no_profit_or_loss")
        self.assertEqual(result["breakeven_trades"], 2)

    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty_trade_sample"):
            analyze_closed_trade_pnl([])

    def test_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_trade_pnl"):
            analyze_closed_trade_pnl(["NaN"])


if __name__ == "__main__":
    unittest.main()
