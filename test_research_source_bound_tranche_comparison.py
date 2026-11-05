import hashlib
import unittest
from research_source_bound_tranche_comparison import compare_source_bound_tranches

class SourceBoundTrancheTests(unittest.TestCase):
    def fixture(self):
        raw = b"frozen hypothetical OHLCV source"
        payload = {"format": "DIPSAUS_HISTORICAL_CANDIDATES_V1",
                   "provenance": {"source": "offline fixture",
                                  "retrieved_at_utc": "2026-11-05T12:00:00Z",
                                  "source_snapshot_sha256": hashlib.sha256(raw).hexdigest()},
                   "candidates": [
                       {"id": "a", "symbol": "AMD", "entry_date": "2026-10-01",
                        "exit_date": "2026-10-15", "realized_return_pct": 2},
                       {"id": "b", "symbol": "META", "entry_date": "2026-10-02",
                        "exit_date": "2026-10-16", "realized_return_pct": -1}]}
        return payload, raw

    def test_verified_bytes_feed_comparison_without_alpha_claim(self):
        payload, raw = self.fixture()
        result = compare_source_bound_tranches(payload, raw,
                                               starting_settled_cash_eur=5000,
                                               tranches_eur=(3500, 5000))
        self.assertTrue(result["source_snapshot_bytes_verified"])
        self.assertEqual(result["comparison"]["candidate_count"], 2)
        self.assertEqual([s["accepted_count"] for s in result["comparison"]["scenarios"]], [1, 1])
        self.assertFalse(result["historical_edge_proven"])
        self.assertFalse(result["source_independently_verified"])

    def test_tampered_source_prevents_comparison(self):
        payload, raw = self.fixture()
        with self.assertRaisesRegex(ValueError, "SOURCE_SNAPSHOT_DIGEST_MISMATCH"):
            compare_source_bound_tranches(payload, raw + b"x",
                                          starting_settled_cash_eur=50000)

    def test_missing_symbol_prevents_comparison(self):
        payload, raw = self.fixture()
        del payload["candidates"][0]["symbol"]
        with self.assertRaisesRegex(ValueError, "MISSING_CANDIDATE_SYMBOL"):
            compare_source_bound_tranches(payload, raw,
                                          starting_settled_cash_eur=50000)

    def test_empty_ledger_is_not_an_experiment(self):
        payload, raw = self.fixture()
        payload["candidates"] = []
        with self.assertRaisesRegex(ValueError, "EMPTY_HISTORICAL_CANDIDATE_LEDGER"):
            compare_source_bound_tranches(payload, raw,
                                          starting_settled_cash_eur=50000)

if __name__ == "__main__":
    unittest.main()
