"""Regression tests for offline source observation verification."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from research_verify_finnhub_observation import verify


class VerifyObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "observation.json"
        raw = b'{"c":100.5,"t":1793737456}'
        self.record = {
            "schema": "dipsaus_research_source_observation_v1",
            "provider": "Finnhub", "endpoint": "/api/v1/quote",
            "symbol_requested": "AMD",
            "request_started_utc": "2026-11-03T20:24:15+00:00",
            "response_finished_utc": "2026-11-03T20:24:16+00:00",
            "raw_response_hex": raw.hex(), "source_bytes": len(raw),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "source_timestamp_claim_unverified": 1793737456,
            "external_receipt_verified": False,
            "provider_identity_independently_verified": False,
            "prospective_signal_proven": False,
            "research_only": True, "trade_ready": False,
        }

    def check(self):
        self.path.write_text(json.dumps(self.record), encoding="utf-8")
        return verify(self.path)

    def test_valid_observation_is_only_integrity_verified(self):
        result = self.check()
        self.assertEqual(result["status"], "offline_integrity_verified")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["provider_authenticated"])

    def test_hash_tampering_rejected(self):
        self.record["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source_hash_mismatch"):
            self.check()

    def test_unsafe_trade_claim_rejected(self):
        self.record["trade_ready"] = True
        with self.assertRaisesRegex(ValueError, "unsafe_evidence_claim"):
            self.check()

    def test_wrong_source_rejected(self):
        self.record["provider"] = "Unknown"
        with self.assertRaisesRegex(ValueError, "unexpected_source"):
            self.check()

    def test_timestamp_inversion_rejected(self):
        self.record["response_finished_utc"] = "2026-11-03T20:24:14+00:00"
        with self.assertRaisesRegex(ValueError, "invalid_observation_clock"):
            self.check()

    def test_raw_response_tampering_rejected(self):
        self.record["raw_response_hex"] = b'{"c":999.5,"t":1793737456}'.hex()
        with self.assertRaises(ValueError):
            self.check()

    def test_source_claim_mismatch_rejected(self):
        self.record["source_timestamp_claim_unverified"] = 0
        with self.assertRaisesRegex(ValueError, "invalid_quote_claim"):
            self.check()

    def test_boolean_price_rejected(self):
        raw = b'{"c":true}'
        self.record["raw_response_hex"] = raw.hex()
        self.record["source_bytes"] = len(raw)
        self.record["source_sha256"] = hashlib.sha256(raw).hexdigest()
        self.record["source_timestamp_claim_unverified"] = None
        with self.assertRaisesRegex(ValueError, "invalid_quote_values"):
            self.check()


if __name__ == "__main__":
    unittest.main()
