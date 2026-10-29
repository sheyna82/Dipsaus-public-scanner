import unittest
from datetime import date, timedelta
from decimal import Decimal
from research.swing_lifecycle.warning_portfolio_comparison import compare_warning_exit_portfolios


def case(ticker="AAA", warning=False):
    start = date(2026, 1, 1)
    bars = [{"date": (start+timedelta(days=i)).isoformat(),
             "open": 100, "high": 101, "low": 99, "close": 100}
            for i in range(32)]
    if warning:
        bars[24].update(open=94, high=95, low=90, close=91)
        bars[25].update(open=89, high=91, low=88, close=90)
        bars[29].update(open=80, high=82, low=79, close=81)
    return {"ticker": ticker, "bars": bars, "entry_index": 21,
            "baseline_exit_index": 29, "score": 10}


class PortfolioWarningComparisonTests(unittest.TestCase):
    def test_no_warning_same_result(self):
        result = compare_warning_exit_portfolios([case()])
        self.assertEqual(Decimal(result["difference_realized_pnl"]), 0)

    def test_warning_reduces_loss_in_declining_synthetic_path(self):
        result = compare_warning_exit_portfolios([case(warning=True)])
        self.assertGreater(Decimal(result["difference_realized_pnl"]), 0)
        self.assertEqual(result["candidate_diagnostics"][0]["candidate_holding_sessions"], 4)

    def test_duplicate_trade_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_trade"):
            compare_warning_exit_portfolios([case(), case()])

    def test_costs_applied_to_both_scenarios(self):
        no_cost = compare_warning_exit_portfolios([case()], cost_bps_per_side=0)
        with_cost = compare_warning_exit_portfolios([case()], cost_bps_per_side=10)
        self.assertGreater(Decimal(no_cost["baseline"]["realized_net_pnl"]),
                           Decimal(with_cost["baseline"]["realized_net_pnl"]))


if __name__ == "__main__":
    unittest.main()
