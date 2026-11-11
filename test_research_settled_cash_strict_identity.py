import unittest
from research_settled_cash import simulate_settled_cash

class StrictSymbolIdentityTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {"id": "c1", "entry_date": "2026-11-02",
                          "exit_date": "2026-11-12", "realized_return_pct": 1}

    def test_missing_symbol_blocks_strict_comparison(self):
        with self.assertRaisesRegex(ValueError, "MISSING_CANDIDATE_SYMBOL"):
            simulate_settled_cash([self.candidate], starting_settled_cash_eur=3500,
                                  require_symbol=True)

    def test_strict_complete_identity_is_reported(self):
        result = simulate_settled_cash([dict(self.candidate, symbol="AMD")],
                                       starting_settled_cash_eur=3500,
                                       require_symbol=True)
        self.assertTrue(result["symbol_identity_required"])
        self.assertTrue(result["symbol_identity_complete"])

    def test_legacy_omitted_symbol_is_explicitly_incomplete(self):
        result = simulate_settled_cash([self.candidate],
                                       starting_settled_cash_eur=3500)
        self.assertFalse(result["symbol_identity_complete"])
        self.assertFalse(result["symbol_identity_required"])

    def test_non_boolean_flag_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_REQUIRE_SYMBOL"):
            simulate_settled_cash([], starting_settled_cash_eur=3500,
                                  require_symbol="yes")

if __name__ == "__main__":
    unittest.main()
