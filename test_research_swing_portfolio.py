"""Synthetic portfolio capacity and capital competition tests."""
import unittest
from decimal import Decimal
from research_swing_portfolio import allocate_and_simulate


def candidate(ticker, score, final=105):
    return {"ticker": ticker, "score": score, "entry_price": 100,
            "daily_closes": [101, 102, 103, 104, final]}


class PortfolioTests(unittest.TestCase):
    def test_top_score_wins_single_tranche(self):
        result = allocate_and_simulate([candidate("LOW", 1, 150),
                                        candidate("HIGH", 9, 90)], 3500)
        self.assertEqual([x["ticker"] for x in result["selected"]], ["HIGH"])
        self.assertEqual(result["portfolio_net_pnl"], "-350.00")

    def test_capacity_six_positions(self):
        result = allocate_and_simulate(
            [candidate(f"T{i}", i) for i in range(9)], 30000)
        self.assertEqual(result["selected_count"], 6)
        self.assertEqual(result["unallocated_capital"], "9000")

    def test_idle_cash_dilutes_return(self):
        a = allocate_and_simulate([candidate("A", 1)], 3500)
        b = allocate_and_simulate([candidate("A", 1)], 7000)
        self.assertEqual(a["portfolio_net_pnl"], b["portfolio_net_pnl"])
        self.assertGreater(Decimal(a["portfolio_return_pct"]),
                           Decimal(b["portfolio_return_pct"]))

    def test_no_position_if_insufficient_tranche(self):
        result = allocate_and_simulate([candidate("A", 1)], 3000)
        self.assertEqual(result["selected_count"], 0)
        self.assertEqual(result["portfolio_net_pnl"], "0.00")

    def test_deterministic_tie_break(self):
        result = allocate_and_simulate(
            [candidate("B", 3), candidate("A", 3)], 3500)
        self.assertEqual(result["selected"][0]["ticker"], "A")

    def test_duplicate_tickers_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            allocate_and_simulate([candidate("A", 1), candidate("A", 2)], 7000)

    def test_costs_reduce_portfolio_profit(self):
        base = allocate_and_simulate([candidate("A", 1)], 3500)
        costly = allocate_and_simulate([candidate("A", 1)], 3500,
                                         spread_bps=10, slippage_bps=5,
                                         commission_bps=2)
        self.assertLess(Decimal(costly["portfolio_net_pnl"]),
                        Decimal(base["portfolio_net_pnl"]))


if __name__ == "__main__":
    unittest.main()
