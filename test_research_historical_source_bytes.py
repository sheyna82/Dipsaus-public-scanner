import hashlib
import unittest
from research_historical_candidate_ledger import verify_historical_source_snapshot

class FrozenSourceBytesTests(unittest.TestCase):
    def fixture(self, raw=b"archived raw source bytes"):
        return {"format": "DIPSAUS_HISTORICAL_CANDIDATES_V1",
                "provenance": {"source": "offline-archive",
                               "retrieved_at_utc": "2026-11-05T12:00:00Z",
                               "source_snapshot_sha256": hashlib.sha256(raw).hexdigest()},
                "candidates": [{"id": "a", "symbol": "AMD",
                                "entry_date": "2026-10-01",
                                "exit_date": "2026-10-15",
                                "realized_return_pct": 2.5}]}

    def test_exact_bytes_match_but_not_independently_verified(self):
        raw = b"archived raw source bytes"
        result = verify_historical_source_snapshot(self.fixture(raw), raw)
        self.assertTrue(result["source_snapshot_bytes_verified"])
        self.assertEqual(result["source_snapshot_byte_length"], len(raw))
        self.assertFalse(result["source_independently_verified"])
        self.assertFalse(result["trade_ready"])

    def test_changed_source_bytes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_SNAPSHOT_DIGEST_MISMATCH"):
            verify_historical_source_snapshot(self.fixture(), b"modified bytes")

    def test_empty_snapshot_rejected(self):
        with self.assertRaisesRegex(ValueError, "EMPTY_SOURCE_SNAPSHOT"):
            verify_historical_source_snapshot(self.fixture(b""), b"")

    def test_nonbyte_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_SOURCE_BYTES"):
            verify_historical_source_snapshot(self.fixture(), "text not bytes")

if __name__ == "__main__":
    unittest.main()
