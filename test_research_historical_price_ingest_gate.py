"""Offline historical price dataset gate regression tests."""
import hashlib
import unittest

from research_historical_price_ingest_gate import audit_historical_price_dataset

PAYLOAD = b"date,open,high,low,close,volume\n2026-01-02,10,12,9,11,100\n"


def manifest(payload=PAYLOAD):
    return {
        "provider": "synthetic fixture",
        "dataset": "synthetic daily bars",
        "source_url": "https://example.org/fixture",
        "license_reference": "test-only synthetic data",
        "retrieved_at": "2026-10-23T10:00:00+00:00",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "adjustment_policy": "unadjusted",
        "universe_policy": "single synthetic symbol",
    }


class HistoricalPriceIngestTests(unittest.TestCase):
    def test_both_gates_pass_without_provenance_claim(self):
        result = audit_historical_price_dataset(manifest(), PAYLOAD)
        self.assertTrue(result["accepted"])
        self.assertTrue(result["manifest_consistent"])
        self.assertTrue(result["ohlcv_structure_valid"])
        self.assertFalse(result["provider_authenticity_verified"])
        self.assertFalse(result["license_verified"])
        self.assertFalse(result["trade_ready"])

    def test_changed_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError, "payload_hash_mismatch"):
            audit_historical_price_dataset(manifest(), PAYLOAD + b"\n")

    def test_valid_hash_cannot_hide_bad_prices(self):
        invalid = b"date,open,high,low,close,volume\n2026-01-02,10,8,9,11,100\n"
        with self.assertRaisesRegex(ValueError, "invalid_ohlcv"):
            audit_historical_price_dataset(manifest(invalid), invalid)


if __name__ == "__main__":
    unittest.main()
