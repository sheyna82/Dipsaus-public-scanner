import unittest
from research_settled_cash import simulate_settled_cash

def c(identifier, symbol, start, end):
    return {"id": identifier, "symbol": symbol, "entry_date": start,
            "exit_date": end, "realized_return_pct": 0}

class SameSymbolCapitalTests(unittest.TestCase):
    def test_overlap_blocks_second_entry_even_with_cash_and_slots(self):
        rows = [c("first", "AMD", "2026-11-02", "2026-11-12"),
                c("second", "amd", "2026-11-04", "2026-11-13")]
        result = simulate_settled_cash(rows, starting_settled_cash_eur=10000)
        self.assertEqual([r["decision"] for r in result["events"]],
                         ["SIMULATED_ACCEPT", "SYMBOL_ALREADY_HELD"])

    def test_different_symbol_still_accepted(self):
        rows = [c("first", "AMD", "2026-11-02", "2026-11-12"),
                c("second", "META", "2026-11-04", "2026-11-13")]
        result = simulate_settled_cash(rows, starting_settled_cash_eur=10000)
        self.assertEqual(result["accepted_count"], 2)

    def test_same_symbol_after_exit_and_settlement(self):
        rows = [c("first", "AMD", "2026-11-02", "2026-11-06"),
                c("second", "AMD", "2026-11-10", "2026-11-17")]
        result = simulate_settled_cash(rows, starting_settled_cash_eur=3500,
                                       settlement_business_days=2,
                                       round_trip_cost_rate=0)
        self.assertEqual(result["accepted_count"], 2)

    def test_missing_symbol_preserves_legacy_inputs(self):
        rows = [{"id": "first", "entry_date": "2026-11-02",
                 "exit_date": "2026-11-12", "realized_return_pct": 0}]
        self.assertEqual(simulate_settled_cash(rows, starting_settled_cash_eur=3500)["accepted_count"], 1)

    def test_invalid_symbol_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "INVALID_CANDIDATE_SYMBOL"):
            simulate_settled_cash([c("x", " ", "2026-11-02", "2026-11-12")],
                                  starting_settled_cash_eur=3500)

if __name__ == "__main__":
    unittest.main()
