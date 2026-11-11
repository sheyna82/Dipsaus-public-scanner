import unittest
from research_trade_capital_efficiency import compare_trade_capital_efficiency

TRADES = [{"return_pct": 5, "holding_days": 5, "mae_pct": -3},
          {"return_pct": -2, "holding_days": 15, "mae_pct": -8}]

class CapitalEfficiencyTests(unittest.TestCase):
    def test_scaling_capital_does_not_fabricate_efficiency(self):
        report = compare_trade_capital_efficiency(TRADES, tranche_sizes=(3500, 7000))
        a, b = report["scenarios"]
        self.assertEqual(b["sample_net_pnl_eur"], 2 * a["sample_net_pnl_eur"])
        self.assertEqual(b["sample_capital_days_eur"], 2 * a["sample_capital_days_eur"])
        self.assertEqual(a["net_pnl_per_1000_eur_capital_days"],
                         b["net_pnl_per_1000_eur_capital_days"])
        self.assertFalse(report["position_sizing_improvement_established"])
        self.assertFalse(report["trade_ready"])

    def test_costs_are_deducted_from_each_trade(self):
        report = compare_trade_capital_efficiency(TRADES, tranche_sizes=(1000,), cost_rate=0.005)
        self.assertEqual(report["scenarios"][0]["sample_net_pnl_eur"], 20.0)

    def test_mae_is_not_misrepresented_as_portfolio_drawdown(self):
        report = compare_trade_capital_efficiency(TRADES, tranche_sizes=(1000,))
        self.assertEqual(report["scenarios"][0]["worst_single_trade_mae_eur_proxy"], -80)
        self.assertIsNone(report["scenarios"][0]["portfolio_drawdown"])

    def test_missing_trade_metrics_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TRADE"):
            compare_trade_capital_efficiency([{"return_pct": 3, "holding_days": 5}])

    def test_invalid_numeric_inputs_fail_closed(self):
        for bad in (True, float("nan"), float("inf"), -1):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    compare_trade_capital_efficiency(
                        [{"return_pct": 1, "holding_days": bad, "mae_pct": -1}])

    def test_loss_below_full_capital_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TRADE_METRICS"):
            compare_trade_capital_efficiency(
                [{"return_pct": -101, "holding_days": 5, "mae_pct": -10}])

if __name__ == "__main__":
    unittest.main()
