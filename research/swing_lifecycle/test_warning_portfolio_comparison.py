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

    def test_warning_can_destroy_upside_in_rebound(self):
        example = case(warning=True)
        example["bars"][29].update(open=120, high=122, low=119, close=121)
        result = compare_warning_exit_portfolios([example])
        self.assertLess(Decimal(result["difference_realized_pnl"]), 0)
        self.assertEqual(result["candidate_diagnostics"][0]["candidate_holding_sessions"], 4)

    def test_warning_releases_capital_earlier(self):
        result = compare_warning_exit_portfolios([case(warning=True)])
        original_exits = [x["date"] for x in result["baseline"]["ledger"]
                          if x["action"] == "exit"]
        guarded_exits = [x["date"] for x in result["warning_protected"]["ledger"]
                         if x["action"] == "exit"]
        self.assertLess(guarded_exits[0], original_exits[0])

    def test_released_cash_can_fund_later_trade(self):
        first = case(ticker="AAA", warning=True)
        second = case(ticker="BBB")
        second["entry_index"] = 26
        second["baseline_exit_index"] = 30
        result = compare_warning_exit_portfolios(
            [first, second], initial_capital=3500,
            tranche=3500, max_positions=1, cost_bps_per_side=0)
        self.assertEqual(result["baseline"]["rejected_count"], 1)
        self.assertEqual(result["warning_protected"]["rejected_count"], 0)
        self.assertEqual(
            [row["ticker"] for row in result["warning_protected"]["ledger"]
             if row["action"] == "entry"], ["AAA", "BBB"])

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
