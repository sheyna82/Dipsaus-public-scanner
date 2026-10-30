"""Synthetic chronology and cash-capacity regressions."""
import unittest
from datetime import date
from decimal import Decimal
from research_swing_chronological_ledger import simulate_chronological_portfolio


def trade(ticker, entry, exit_, pct, score=1):
    return {"ticker": ticker, "entry_date": date(2026, 1, entry),
            "exit_date": date(2026, 1, exit_),
            "net_return_pct": pct, "score": score}


class ChronologicalLedgerTests(unittest.TestCase):
    def test_reinvest_only_after_exit_date(self):
        rows = [trade("A", 2, 5, 10), trade("B", 5, 8, 20),
                trade("C", 6, 9, -10)]
        r = simulate_chronological_portfolio(rows, initial_capital=3500,
                                              tranche=3500, max_positions=1)
        self.assertEqual([(x["ticker"], x["action"]) for x in r["ledger"]],
                         [("A", "entry"), ("A", "exit"),
                          ("C", "entry"), ("C", "exit")])
        self.assertEqual(Decimal(r["ending_cash"]), Decimal("3500"))
        self.assertEqual(r["rejected_entries"],
                         [{"date": "2026-01-05", "ticker": "B",
                           "reason": "position_cap"}])

    def test_cap_and_score_tie(self):
        rows = [trade("Z", 2, 5, 10), trade("A", 2, 5, -10),
                trade("B", 2, 5, 20)]
        r = simulate_chronological_portfolio(rows, initial_capital=7000,
                                              tranche=3500, max_positions=2)
        self.assertEqual([x["ticker"] for x in r["ledger"] if x["action"] == "entry"],
                         ["A", "B"])
        self.assertEqual(Decimal(r["realized_net_pnl"]), Decimal("350"))

    def test_overlapping_same_ticker_not_duplicated(self):
        r = simulate_chronological_portfolio(
            [trade("A", 2, 6, 10), trade("A", 3, 7, 20)])
        self.assertEqual(sum(x["action"] == "entry" for x in r["ledger"]), 1)
        self.assertEqual(r["rejected_entries"][0]["reason"], "already_held")

    def test_rejects_invalid_returns(self):
        with self.assertRaisesRegex(ValueError, "invalid_return"):
            simulate_chronological_portfolio([trade("A", 2, 4, -101)])


if __name__ == "__main__":
    unittest.main()
