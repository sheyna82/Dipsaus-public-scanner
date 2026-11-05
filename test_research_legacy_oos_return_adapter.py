import unittest
from datetime import date
from research_legacy_oos_return_adapter import adapt_legacy_oos_net_candidates

def day(iso):
    return (date.fromisoformat(iso) - date(1970, 1, 1)).days

def record(symbol="AMD", ret=3.0):
    return {"symbol": symbol, "entry_day": day("2026-10-01"),
            "exit_day": day("2026-10-15"), "net_return_pct": ret}

class LegacyOosAdapterTests(unittest.TestCase):
    def test_old_net_return_restores_gross_before_new_cost(self):
        result = adapt_legacy_oos_net_candidates([record()], legacy_cost_bps=20,
                                                  simulator_round_trip_cost_rate=.002)
        self.assertAlmostEqual(result["candidates"][0]["realized_return_pct"], 3.2)
        self.assertTrue(result["legacy_fee_model_equivalent_to_simulator"])
        self.assertFalse(result["source_independently_verified"])

    def test_different_cost_assumption_is_explicit(self):
        result = adapt_legacy_oos_net_candidates([record()], legacy_cost_bps=20,
                                                  simulator_round_trip_cost_rate=.005)
        self.assertFalse(result["legacy_fee_model_equivalent_to_simulator"])
        self.assertAlmostEqual(result["candidates"][0]["realized_return_pct"], 3.2)

    def test_duplicate_symbol_and_entry_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_LEGACY_CANDIDATE"):
            adapt_legacy_oos_net_candidates([record(), record("amd")],
                                            legacy_cost_bps=20,
                                            simulator_round_trip_cost_rate=.002)

    def test_missing_symbol_rejected(self):
        with self.assertRaisesRegex(ValueError, "MISSING_CANDIDATE_SYMBOL"):
            adapt_legacy_oos_net_candidates([record("")], legacy_cost_bps=20,
                                            simulator_round_trip_cost_rate=.002)

    def test_symbol_grouped_rows_are_sorted_by_entry_date(self):
        later = record("AMD")
        earlier = record("META")
        later["entry_day"] = day("2026-10-10")
        later["exit_day"] = day("2026-10-20")
        result = adapt_legacy_oos_net_candidates([later, earlier],
            legacy_cost_bps=50, simulator_round_trip_cost_rate=.005)
        self.assertEqual([x["symbol"] for x in result["candidates"]], ["META", "AMD"])
        self.assertTrue(result["chronological_order_normalized"])

    def test_same_day_input_order_is_stable(self):
        result = adapt_legacy_oos_net_candidates([record("META"), record("AMD")],
            legacy_cost_bps=50, simulator_round_trip_cost_rate=.005)
        self.assertEqual([x["symbol"] for x in result["candidates"]], ["META", "AMD"])

    def test_invalid_return_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_LEGACY_RETURN"):
            adapt_legacy_oos_net_candidates([record(ret=float("nan"))],
                                            legacy_cost_bps=20,
                                            simulator_round_trip_cost_rate=.002)

if __name__ == "__main__":
    unittest.main()
