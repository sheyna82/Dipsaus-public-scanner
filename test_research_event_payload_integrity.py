"""Offline SHA256 market evidence regression, using synthetic bytes."""
import hashlib
import unittest
from research_event_payload_integrity import verify_market_payload


class PayloadIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.payload = b"synthetic,not-a-real-market-price\n"
        self.record = {
            "symbol": "AMD",
            "observation_timestamp_utc": "2026-10-23T20:00:00Z",
            "retrieved_at_utc": "2026-10-24T08:00:00Z",
            "source_url": "https://example.org/synthetic",
            "content_sha256": hashlib.sha256(self.payload).hexdigest(),
            "exchange": "XNYS",
            "currency": "USD",
        }

    def verify(self, payload=None):
        return verify_market_payload(self.record,
                                     self.payload if payload is None else payload,
                                     "2026-10-24T12:00:00Z")

    def test_digest_match_does_not_prove_source_authenticity(self):
        result = self.verify()
        self.assertTrue(result["digest_matches_supplied_payload"])
        self.assertFalse(result["source_authenticity_verified"])
        self.assertFalse(result["price_data_semantics_verified"])
        self.assertFalse(result["trade_ready"])

    def test_tampered_or_oversized_payload_rejected(self):
        with self.assertRaisesRegex(ValueError, "market_payload_digest_mismatch"):
            self.verify(b"tampered")
        with self.assertRaisesRegex(ValueError, "market_payload_size_invalid"):
            self.verify(b"x" * 5_000_001)
        with self.assertRaisesRegex(ValueError, "market_payload_must_be_bytes"):
            self.verify("string")


if __name__ == "__main__":
    unittest.main()
