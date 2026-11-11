import unittest
from research_settled_cash import simulate_settled_cash as simulate

def trade(i, start, end, ret=0):
    return {"id": i, "entry_date": start, "exit_date": end,
            "realized_return_pct": ret}

class SettledCashTests(unittest.TestCase):
    def test_same_day_exit_cannot_fund_new_entry_with_two_day_lag(self):
        result = simulate([trade("A", "2026-01-05", "2026-01-12"),
                           trade("B", "2026-01-12", "2026-01-20")],
                          starting_settled_cash_eur=3500, round_trip_cost_rate=0)
        self.assertEqual([e["decision"] for e in result["events"]],
                         ["SIMULATED_ACCEPT", "INSUFFICIENT_SETTLED_CASH"])

    def test_cash_can_be_reused_after_settlement(self):
        result = simulate([trade("A", "2026-01-05", "2026-01-12"),
                           trade("B", "2026-01-14", "2026-01-20")],
                          starting_settled_cash_eur=3500, round_trip_cost_rate=0)
        self.assertEqual(result["accepted_count"], 2)

    def test_loss_reduces_settled_proceeds(self):
        result = simulate([trade("A", "2026-01-05", "2026-01-12", -10),
                           trade("B", "2026-01-14", "2026-01-20")],
                          starting_settled_cash_eur=3500, round_trip_cost_rate=0)
        self.assertEqual(result["accepted_count"], 1)
        self.assertEqual(result["cash_after_last_entry_eur"], 3150)

    def test_position_slot_released_before_cash(self):
        result = simulate([trade("A", "2026-01-05", "2026-01-12"),
                           trade("B", "2026-01-12", "2026-01-20")],
                          starting_settled_cash_eur=7000, max_positions=1,
                          round_trip_cost_rate=0)
        self.assertEqual(result["accepted_count"], 2)

    def test_outcome_does_not_reorder_candidates(self):
        trades = [trade("A", "2026-01-05", "2026-01-20", 100),
                  trade("B", "2026-01-06", "2026-01-21", -50)]
        changed = [dict(trades[0], realized_return_pct=-100), trades[1]]
        a = simulate(trades, starting_settled_cash_eur=3500)
        b = simulate(changed, starting_settled_cash_eur=3500)
        self.assertEqual([e["decision"] for e in a["events"]],
                         [e["decision"] for e in b["events"]])

    def test_invalid_lag_rejected(self):
        for lag in (-1, True, 1.5):
            with self.subTest(lag=lag):
                with self.assertRaisesRegex(ValueError, "INVALID_SETTLEMENT_DAYS"):
                    simulate([], starting_settled_cash_eur=3500,
                             settlement_calendar_days=lag)

if __name__ == "__main__":
    unittest.main()
