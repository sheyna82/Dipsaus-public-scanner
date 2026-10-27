"""Integration tests for chronological ledger and marked equity."""
import unittest
from datetime import date
from decimal import Decimal
from research_swing_portfolio_with_marks import backtest_portfolio_with_marks


class PortfolioWithMarksTests(unittest.TestCase):
    def test_multi_position_cash_and_drawdown(self):
        d = lambda n: date(2026, 1, n)
        trades = [
            {"ticker": "A", "entry_date": d(2), "exit_date": d(6),
             "net_return_pct": 10, "score": 2},
            {"ticker": "B", "entry_date": d(2), "exit_date": d(6),
             "net_return_pct": -10, "score": 1},
        ]
        dates = [d(2), d(5), d(6)]
        marks = {(d(2), "A"): 3500, (d(2), "B"): 3500,
                 (d(5), "A"): 2800, (d(5), "B"): 2800}
        result = backtest_portfolio_with_marks(
            trades, marks, dates, initial_capital=7000,
            tranche=3500, max_positions=2)
        self.assertEqual(Decimal(result["cash_accounting"]["ending_cash"]),
                         Decimal("7000"))
        self.assertEqual(Decimal(result["equity"]["ending_equity"]),
                         Decimal("7000"))
        self.assertEqual(Decimal(result["equity"]["max_drawdown_pct"]),
                         Decimal("-20"))

    def test_missing_mark_fails_closed(self):
        d = lambda n: date(2026, 1, n)
        trades = [{"ticker": "A", "entry_date": d(2),
                   "exit_date": d(5), "net_return_pct": 0, "score": 1}]
        with self.assertRaisesRegex(ValueError, "missing_daily_mark"):
            backtest_portfolio_with_marks(
                trades, {}, [d(2), d(5)], initial_capital=3500)


if __name__ == "__main__":
    unittest.main()
