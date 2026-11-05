import unittest
from research_historical_candidate_ledger import validate_historical_candidate_ledger

def fixture():
    return {"format": "DIPSAUS_HISTORICAL_CANDIDATES_V1",
            "provenance": {"source": "offline-archive", "retrieved_at_utc": "2026-11-05T12:00:00Z",
                           "source_snapshot_sha256": "a" * 64},
            "candidates": [{"id": "a", "symbol": "amd", "entry_date": "2026-10-01",
                            "exit_date": "2026-10-15", "realized_return_pct": 2.5}]}

class HistoricalLedgerGateTests(unittest.TestCase):
    def test_valid_structural_data_not_mislabeled_verified(self):
        result = validate_historical_candidate_ledger(fixture())
        self.assertEqual(result["candidates"][0]["symbol"], "AMD")
        self.assertFalse(result["source_independently_verified"])
        self.assertFalse(result["source_snapshot_bytes_verified"])
        self.assertFalse(result["trade_ready"])
        self.assertEqual(len(result["candidate_sha256"]), 64)

    def test_missing_source_digest_rejected(self):
        x = fixture()
        x["provenance"]["source_snapshot_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "INVALID_SOURCE_DIGEST"):
            validate_historical_candidate_ledger(x)

    def test_duplicate_id_rejected(self):
        x = fixture()
        x["candidates"].append(dict(x["candidates"][0]))
        with self.assertRaisesRegex(ValueError, "INVALID_CANDIDATE_ID"):
            validate_historical_candidate_ledger(x)

    def test_missing_symbol_rejected(self):
        x = fixture()
        del x["candidates"][0]["symbol"]
        with self.assertRaisesRegex(ValueError, "MISSING_CANDIDATE_SYMBOL"):
            validate_historical_candidate_ledger(x)

    def test_invalid_dates_rejected(self):
        x = fixture()
        x["candidates"][0]["exit_date"] = "2026-09-30"
        with self.assertRaisesRegex(ValueError, "INVALID_CANDIDATE_DATES"):
            validate_historical_candidate_ledger(x)

    def test_nonfinite_outcome_rejected(self):
        x = fixture()
        x["candidates"][0]["realized_return_pct"] = float("nan")
        with self.assertRaisesRegex(ValueError, "INVALID_CANDIDATE_OUTCOME"):
            validate_historical_candidate_ledger(x)

if __name__ == "__main__":
    unittest.main()
