"""Synthetic daily equity/drawdown regression tests."""
import unittest
from datetime import date
from decimal import Decimal
from research_swing_chronological_ledger import simulate_chronological_portfolio
from research_swing_daily_equity import daily_equity_from_ledger


class DailyEquityTests(unittest.TestCase):
    def test_drawdown_then_recovery(self):
        d = lambda n: date(2026, 1, n)
        ledger = simulate_chronological_portfolio([
            {"ticker": "A", "entry_date": d(2), "exit_date": d(6),
             "net_return_pct": 10, "score": 1}],
            initial_capital=3500, tranche=3500)["ledger"]
        days = [d(2), d(5), d(6)]
        marks = {(d(2), "A"): 3500, (d(5), "A"): 2800}
        result = daily_equity_from_ledger(
            ledger, marks, days, initial_capital=3500, tranche=3500)
        self.assertEqual(Decimal(result["max_drawdown_pct"]), Decimal("-20"))
        self.assertEqual(Decimal(result["ending_equity"]), Decimal("3850"))

    def test_missing_mark_rejected(self):
        ledger = [{"date": "2026-01-02", "ticker": "A",
                   "action": "entry", "cash": "0"},
                  {"date": "2026-01-06", "ticker": "A",
                   "action": "exit", "cash": "3850"}]
        with self.assertRaisesRegex(ValueError, "missing_daily_mark"):
            daily_equity_from_ledger(
                ledger, {}, [date(2026, 1, 2), date(2026, 1, 6)],
                initial_capital=3500)

    def test_missing_exit_session_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_trading_dates"):
            daily_equity_from_ledger(
                [{"date": "2026-01-06", "ticker": "A",
                  "action": "exit", "cash": "3850"}], {},
                [date(2026, 1, 5)])


if __name__ == "__main__":
    unittest.main()
