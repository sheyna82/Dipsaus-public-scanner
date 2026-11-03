"""Tests for verified Finnhub observation inventory."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from research_finnhub_observation_inventory import build_inventory


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def observation(self, filename, symbol="AMD", minute="15", price=100):
        raw = json.dumps({"c": price, "t": 1793737456}, separators=(",", ":")).encode()
        record = {
            "schema": "dipsaus_research_source_observation_v1",
            "provider": "Finnhub", "endpoint": "/api/v1/quote",
            "symbol_requested": symbol,
            "request_started_utc": f"2026-11-03T20:24:{minute}+00:00",
            "response_finished_utc": f"2026-11-03T20:25:{minute}+00:00",
            "raw_response_hex": raw.hex(), "source_bytes": len(raw),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "source_timestamp_claim_unverified": 1793737456,
            "external_receipt_verified": False,
            "provider_identity_independently_verified": False,
            "prospective_signal_proven": False,
            "research_only": True, "trade_ready": False,
        }
        p = self.root / filename
        p.write_text(json.dumps(record), encoding="utf-8")
        return p

    def test_one_verified_record(self):
        inventory = build_inventory([self.observation("one.json")])
        self.assertEqual(inventory["count"], 1)
        self.assertFalse(inventory["trade_ready"])

    def test_deterministic_order(self):
        first = self.observation("first.json", minute="15")
        second = self.observation("second.json", minute="16")
        self.assertEqual(build_inventory([second, first]), build_inventory([first, second]))

    def test_duplicate_window_rejected(self):
        p = self.observation("one.json")
        with self.assertRaisesRegex(ValueError, "duplicate_observation_window"):
            build_inventory([p, p])

    def test_conflicting_same_window_rejected(self):
        a = self.observation("one.json", price=100)
        b = self.observation("two.json", price=101)
        with self.assertRaisesRegex(ValueError, "duplicate_observation_window"):
            build_inventory([a, b])

    def test_tampering_rejected(self):
        p = self.observation("one.json")
        record = json.loads(p.read_text())
        record["source_sha256"] = "0" * 64
        p.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "source_hash_mismatch"):
            build_inventory([p])

    def test_empty_inventory_rejected(self):
        with self.assertRaisesRegex(ValueError, "observation_paths_required"):
            build_inventory([])

    def test_multiple_symbols_supported(self):
        a = self.observation("a.json", symbol="AMD")
        b = self.observation("b.json", symbol="COHU")
        self.assertEqual(build_inventory([a, b])["count"], 2)


if __name__ == "__main__":
    unittest.main()
