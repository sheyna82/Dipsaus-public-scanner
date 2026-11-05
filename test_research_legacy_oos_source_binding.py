import hashlib
import unittest
from datetime import date
from research_legacy_oos_source_binding import prepare_legacy_oos_source_bound_ledger

def epoch_day(s):
    return (date.fromisoformat(s) - date(1970, 1, 1)).days

class LegacySourceBindingTests(unittest.TestCase):
    def call(self, raw=b"frozen legacy snapshot", rows=None):
        if rows is None:
            rows = [{"symbol": "AMD", "entry_day": epoch_day("2026-10-01"),
                     "exit_day": epoch_day("2026-10-15"), "net_return_pct": 2.0}]
        return prepare_legacy_oos_source_bound_ledger(
            rows, raw, source_name="offline frozen source",
            retrieved_at_utc="2026-11-05T12:00:00Z",
            legacy_cost_bps=50, simulator_round_trip_cost_rate=.005)

    def test_source_digest_and_cost_convention_are_preserved(self):
        raw = b"frozen legacy snapshot"
        result = self.call(raw)
        self.assertEqual(result["source_snapshot_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertTrue(result["source_snapshot_bytes_verified"])
        self.assertTrue(result["legacy_fee_model_equivalent_to_simulator"])
        self.assertAlmostEqual(result["ledger"]["candidates"][0]["realized_return_pct"], 2.5)
        self.assertFalse(result["candidates_rederived_from_snapshot"])
        self.assertFalse(result["trade_ready"])

    def test_empty_snapshot_fails(self):
        with self.assertRaisesRegex(ValueError, "INVALID_FROZEN_SOURCE_BYTES"):
            self.call(b"")

    def test_empty_candidate_pool_fails(self):
        with self.assertRaisesRegex(ValueError, "EMPTY_LEGACY_OOS_CANDIDATES"):
            self.call(rows=[])

    def test_invalid_outcome_fails(self):
        rows = [{"symbol": "AMD", "entry_day": epoch_day("2026-10-01"),
                 "exit_day": epoch_day("2026-10-15"), "net_return_pct": float("nan")}]
        with self.assertRaisesRegex(ValueError, "INVALID_LEGACY_RETURN"):
            self.call(rows=rows)

if __name__ == "__main__":
    unittest.main()
