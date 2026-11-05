import unittest
from research_realized_cashflows import simulate_realized_cashflows as simulate

def trade(identifier, entry, exit_day, ret):
    return {"id": identifier, "entry_date": entry, "exit_date": exit_day,
            "realized_return_pct": ret}

class RealizedCashflowTests(unittest.TestCase):
    def test_loss_reduces_cash_available_for_next_trade(self):
        result = simulate([
            trade("LOSS", "2026-01-05", "2026-01-12", -10),
            trade("NEXT", "2026-01-12", "2026-01-20", 5)],
            starting_cash_eur=3500, round_trip_cost_rate=0)
        self.assertEqual([x["decision"] for x in result["events"]],
                         ["SIMULATED_ACCEPT", "INSUFFICIENT_SIMULATED_CASH"])
        self.assertEqual(result["realized_pnl_from_closed_positions_eur"], -350)

    def test_profit_releases_realized_proceeds(self):
        result = simulate([
            trade("WIN", "2026-01-05", "2026-01-12", 10),
            trade("NEXT", "2026-01-12", "2026-01-20", -5)],
            starting_cash_eur=3500, round_trip_cost_rate=0)
        self.assertEqual(result["accepted_count"], 2)
        self.assertEqual(result["realized_pnl_from_closed_positions_eur"], 350)

    def test_future_outcome_cannot_change_first_entry(self):
        base = [trade("A", "2026-01-05", "2026-01-20", 100),
                trade("B", "2026-01-06", "2026-01-21", -50)]
        alternate = [dict(base[0], realized_return_pct=-100), base[1]]
        first = simulate(base, starting_cash_eur=3500)
        second = simulate(alternate, starting_cash_eur=3500)
        self.assertEqual([e["decision"] for e in first["events"]],
                         [e["decision"] for e in second["events"]])
        self.assertFalse(any(e["outcome_used_for_entry"] for e in first["events"]))

    def test_cost_deducted_at_exit(self):
        result = simulate([
            trade("A", "2026-01-05", "2026-01-12", 0),
            trade("B", "2026-01-12", "2026-01-20", 0)],
            starting_cash_eur=3500, round_trip_cost_rate=0.005)
        self.assertEqual(result["realized_pnl_from_closed_positions_eur"], -17.5)
        self.assertEqual(result["accepted_count"], 1)

    def test_open_trade_proceeds_not_prematurely_credited(self):
        result = simulate([trade("A", "2026-01-05", "2026-01-12", 20)],
                          starting_cash_eur=3500)
        self.assertEqual(result["cash_after_last_entry_eur"], 0)
        self.assertEqual(result["realized_pnl_from_closed_positions_eur"], 0)
        self.assertEqual(result["unsettled_simulated_positions"], 1)

    def test_invalid_return_fails_closed(self):
        for ret in (True, float("nan"), -101, None):
            with self.subTest(ret=ret):
                with self.assertRaisesRegex(ValueError, "INVALID_CANDIDATE_OUTCOME"):
                    simulate([trade("A", "2026-01-05", "2026-01-12", ret)],
                             starting_cash_eur=3500)

if __name__ == "__main__":
    unittest.main()
