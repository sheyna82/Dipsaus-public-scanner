import unittest
from research_tranche_capacity_comparison import compare_tranche_capacity

def candidate(identifier, symbol, start, end):
    return {"id": identifier, "symbol": symbol, "entry_date": start,
            "exit_date": end, "realized_return_pct": 0}

class TrancheCapacityComparisonTests(unittest.TestCase):
    def test_same_candidates_different_capital_pressure(self):
        rows = [candidate("a", "AMD", "2026-11-02", "2026-11-12"),
                candidate("b", "META", "2026-11-03", "2026-11-13"),
                candidate("c", "COHU", "2026-11-04", "2026-11-14")]
        result = compare_tranche_capacity(rows, starting_settled_cash_eur=10000,
                                          tranches_eur=(3500, 5000, 10000))
        self.assertEqual([s["accepted_count"] for s in result["scenarios"]], [2, 2, 1])
        self.assertEqual([s["rejection_reasons"]["INSUFFICIENT_SETTLED_CASH"]
                          for s in result["scenarios"]], [1, 1, 2])
        self.assertFalse(result["best_tranche_identified"])

    def test_strict_identity_required(self):
        rows = [candidate("a", "AMD", "2026-11-02", "2026-11-12")]
        del rows[0]["symbol"]
        with self.assertRaisesRegex(ValueError, "MISSING_CANDIDATE_SYMBOL"):
            compare_tranche_capacity(rows, starting_settled_cash_eur=50000)

    def test_duplicate_tranches_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_TRANCHES"):
            compare_tranche_capacity([], starting_settled_cash_eur=50000,
                                     tranches_eur=(3500, 3500.0))

    def test_overlapping_same_symbol_rejected_across_scenarios(self):
        rows = [candidate("a", "AMD", "2026-11-02", "2026-11-12"),
                candidate("b", "amd", "2026-11-03", "2026-11-13")]
        result = compare_tranche_capacity(rows, starting_settled_cash_eur=50000)
        self.assertTrue(all(s["rejection_reasons"]["SYMBOL_ALREADY_HELD"] == 1
                            for s in result["scenarios"]))

    def test_empty_stream(self):
        result = compare_tranche_capacity([], starting_settled_cash_eur=50000)
        self.assertEqual(len(result["scenarios"]), 4)
        self.assertTrue(all(s["accepted_count"] == 0 for s in result["scenarios"]))

if __name__ == "__main__":
    unittest.main()
