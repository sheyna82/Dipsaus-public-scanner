import unittest
from datetime import date
from research_settled_cash import simulate_settled_cash

def trade(name, entry, exit_date):
    return {"id": name, "entry_date": entry, "exit_date": exit_date,
            "realized_return_pct": 0}

class IntegratedBusinessSettlementTests(unittest.TestCase):
    def test_friday_exit_monday_entry_still_unsettled(self):
        r = simulate_settled_cash([
            trade("A", "2026-11-02", "2026-11-06"),
            trade("B", "2026-11-09", "2026-11-16")],
            starting_settled_cash_eur=3500, round_trip_cost_rate=0,
            settlement_business_days=2)
        self.assertEqual([x["decision"] for x in r["events"]],
                         ["SIMULATED_ACCEPT", "INSUFFICIENT_SETTLED_CASH"])
        self.assertTrue(r["business_day_settlement_modeled"])

    def test_tuesday_entry_can_use_friday_exit(self):
        r = simulate_settled_cash([
            trade("A", "2026-11-02", "2026-11-06"),
            trade("B", "2026-11-10", "2026-11-17")],
            starting_settled_cash_eur=3500, round_trip_cost_rate=0,
            settlement_business_days=2)
        self.assertEqual(r["accepted_count"], 2)

    def test_holiday_delays_tuesday_reuse(self):
        r = simulate_settled_cash([
            trade("A", "2026-11-02", "2026-11-06"),
            trade("B", "2026-11-10", "2026-11-17")],
            starting_settled_cash_eur=3500, round_trip_cost_rate=0,
            settlement_business_days=2, settlement_holidays=(date(2026, 11, 9),))
        self.assertEqual(r["accepted_count"], 1)

    def test_legacy_calendar_day_mode_remains_available(self):
        r = simulate_settled_cash([
            trade("A", "2026-11-02", "2026-11-06"),
            trade("B", "2026-11-09", "2026-11-17")],
            starting_settled_cash_eur=3500, round_trip_cost_rate=0,
            settlement_calendar_days=2)
        self.assertEqual(r["accepted_count"], 2)
        self.assertFalse(r["business_day_settlement_modeled"])

    def test_invalid_calendar_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "INVALID_HOLIDAY_CALENDAR"):
            simulate_settled_cash([], starting_settled_cash_eur=3500,
                                  settlement_business_days=2,
                                  settlement_holidays=("2026-11-09",))

if __name__ == "__main__":
    unittest.main()
