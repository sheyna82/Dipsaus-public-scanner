import unittest
from research_settled_cash import simulate_settled_cash

def row(identifier, symbol, start, end):
    return {"id": identifier, "symbol": symbol, "entry_date": start,
            "exit_date": end, "realized_return_pct": 0}

class CapitalRejectionAccountingTests(unittest.TestCase):
    def test_all_reasons_and_counts_reconcile(self):
        candidates = [
            row("a", "AMD", "2026-11-02", "2026-11-12"),
            row("b", "amd", "2026-11-03", "2026-11-13"),
            row("c", "META", "2026-11-04", "2026-11-13"),
            row("d", "COHU", "2026-11-05", "2026-11-13"),
        ]
        result = simulate_settled_cash(candidates, starting_settled_cash_eur=7000,
                                       max_positions=2)
        self.assertEqual(result["accepted_count"], 2)
        self.assertEqual(result["rejected_count"], 2)
        self.assertEqual(result["rejection_reasons"],
                         {"SYMBOL_ALREADY_HELD": 1, "POSITION_LIMIT": 1,
                          "INSUFFICIENT_SETTLED_CASH": 0})
        self.assertEqual(result["accepted_count"] + result["rejected_count"],
                         len(candidates))

    def test_cash_rejection_when_slots_available(self):
        result = simulate_settled_cash([
            row("a", "AMD", "2026-11-02", "2026-11-12"),
            row("b", "META", "2026-11-03", "2026-11-13")],
            starting_settled_cash_eur=3500)
        self.assertEqual(result["rejection_reasons"]["INSUFFICIENT_SETTLED_CASH"], 1)

    def test_empty_candidates_have_zero_rejections(self):
        result = simulate_settled_cash([], starting_settled_cash_eur=3500)
        self.assertEqual(result["rejected_count"], 0)
        self.assertEqual(sum(result["rejection_reasons"].values()), 0)

if __name__ == "__main__":
    unittest.main()
