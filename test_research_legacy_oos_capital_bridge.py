import unittest
from datetime import date
from research_legacy_oos_capital_bridge import compare_legacy_oos_capital

def epoch_day(s):
    return (date.fromisoformat(s) - date(1970, 1, 1)).days

class LegacyOosCapitalBridgeTests(unittest.TestCase):
    def candidates(self):
        return [
            {"symbol": "AMD", "entry_day": epoch_day("2026-10-01"),
             "exit_day": epoch_day("2026-10-15"), "net_return_pct": 2},
            {"symbol": "META", "entry_day": epoch_day("2026-10-02"),
             "exit_day": epoch_day("2026-10-16"), "net_return_pct": -1}]

    def run_bridge(self, rows):
        return compare_legacy_oos_capital(
            rows, b"illustrative frozen raw source",
            source_name="synthetic fixture", retrieved_at_utc="2026-11-05T12:00:00Z",
            starting_settled_cash_eur=5000, tranches_eur=(3500, 5000))

    def test_end_to_end_capacity_remains_research_only(self):
        result = self.run_bridge(self.candidates())
        self.assertEqual(result["candidate_count"], 2)
        self.assertEqual([s["accepted_count"] for s in result["comparison"]["scenarios"]], [1, 1])
        self.assertTrue(result["legacy_fee_model_equivalent_to_simulator"])
        self.assertFalse(result["candidates_rederived_from_snapshot"])
        self.assertFalse(result["historical_edge_proven"])
        self.assertFalse(result["trade_ready"])

    def test_duplicate_legacy_candidate_fails(self):
        rows = self.candidates()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_LEGACY_CANDIDATE"):
            self.run_bridge(rows + [rows[0]])

    def test_incompatible_fee_model_blocks_comparison(self):
        with self.assertRaisesRegex(ValueError, "LEGACY_SIMULATOR_COST_MODEL_MISMATCH"):
            compare_legacy_oos_capital(
                self.candidates(), b"frozen source", source_name="fixture",
                retrieved_at_utc="2026-11-05T12:00:00Z",
                starting_settled_cash_eur=5000,
                legacy_cost_bps=50, simulator_round_trip_cost_rate=0.01)

    def test_missing_source_bytes_fails(self):
        with self.assertRaisesRegex(ValueError, "INVALID_FROZEN_SOURCE_BYTES"):
            compare_legacy_oos_capital(
                self.candidates(), b"", source_name="fixture",
                retrieved_at_utc="2026-11-05T12:00:00Z",
                starting_settled_cash_eur=5000)

if __name__ == "__main__":
    unittest.main()
