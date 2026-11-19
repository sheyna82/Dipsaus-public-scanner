"""Regression tests for isolated EUR portfolio research only."""
import unittest
from isolated_50000_portfolio_ledger import simulate_research

def trade(ident, entry="2026-11-02", exit="2026-11-05", allocation="3500", pnl="0"):
    return {"id": ident, "entry_date": entry, "exit_date": exit,
            "allocation_eur": allocation, "realized_net_pnl_eur": pnl,
            "research_only": True, "trade_ready": False}

class IsolatedPortfolioTests(unittest.TestCase):
    def test_starting_cash_and_no_orders(self):
        result = simulate_research([])
        self.assertEqual(result["ending_cash_eur"], "50000")
        self.assertFalse(result["broker_connected"])
        self.assertFalse(result["orders_generated"])
        self.assertFalse(result["trade_ready"])

    def test_realized_gain_and_loss(self):
        result = simulate_research([trade("A", pnl="125.50"), trade("B", pnl="-75.25")])
        self.assertEqual(result["ending_cash_eur"], "50050.25")
        self.assertEqual(result["realized_net_pnl_eur"], "50.25")

    def test_rejected_outcome_never_affects_cash(self):
        result = simulate_research([trade("A", allocation="50000", pnl="-1000"),
                                    trade("B", allocation="50000", pnl="999999")])
        self.assertEqual(result["accepted_ids"], ["A"])
        self.assertEqual(result["ending_cash_eur"], "49000")
        self.assertEqual(result["realized_net_pnl_eur"], "-1000")

    def test_conservative_same_day_cash_policy(self):
        rows = [trade("A", allocation="50000"),
                trade("B", entry="2026-11-05", exit="2026-11-09", allocation="50000")]
        self.assertEqual(simulate_research(rows)["accepted_ids"], ["A"])
        self.assertEqual(simulate_research(rows, same_day_cash_reuse=True)["accepted_ids"], ["A", "B"])

    def test_position_limit(self):
        result = simulate_research([trade(str(i)) for i in range(7)])
        self.assertEqual(len(result["accepted_ids"]), 6)

    def test_bad_outcomes_block(self):
        for pnl in ("NaN", "-3500.01", "Infinity"):
            with self.subTest(pnl=pnl), self.assertRaises(ValueError):
                simulate_research([trade("A", pnl=pnl)])

    def test_duplicate_and_invalid_status_block(self):
        with self.assertRaises(ValueError):
            simulate_research([trade("A"), trade("A")])
        row = trade("A")
        row["trade_ready"] = True
        with self.assertRaises(ValueError):
            simulate_research([row])

    def test_future_pnl_not_released_before_exit(self):
        result = simulate_research([trade("A", allocation="50000", pnl="1000"),
                                    trade("B", entry="2026-11-03", exit="2026-11-07",
                                          allocation="1000")])
        self.assertEqual(result["accepted_ids"], ["A"])
        self.assertEqual(result["ending_cash_eur"], "51000")

if __name__ == "__main__":
    unittest.main()
