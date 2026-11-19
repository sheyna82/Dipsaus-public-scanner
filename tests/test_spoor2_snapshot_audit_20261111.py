"""Test offline snapshot provenance and fail-closed schema audit."""
import hashlib
import json
import unittest
from research.spoor2_snapshot_audit_20261111 import audit_snapshots


class SnapshotAuditTests(unittest.TestCase):
    def test_audit_counts_and_byte_hashes(self):
        us = {"latest_us_reports": {"batch_1.json": {"candidates": [
            {"symbol": "TEST", "last_close_usd": 12,
             "recovery_map": {"recent_10d_low_invalidation_reference_usd": 10,
                              "historical_overhead_pivot_zones": [{"low_usd": 14}]}}
        ]}}}
        eu = {"latest_eu_report": {"candidates": [
            {"symbol": "TEST.EU", "currency": "GBp", "historical_close": 120,
             "historical_first_friction": {"price": 125},
             "historical_meaningful_resistance": {"price": 135}}
        ]}}
        us_bytes = json.dumps(us).encode()
        result = audit_snapshots(us_bytes, json.dumps(eu).encode())
        self.assertEqual(result["sources"]["US"]["sha256"],
                         hashlib.sha256(us_bytes).hexdigest())
        self.assertEqual(result["sources"]["US"]["reports"][0]["blocked"], 0)
        self.assertEqual(result["sources"]["EU"]["reports"][0]["total"], 1)
        self.assertFalse(result["trade_ready"])

    def test_malformed_json_and_report_fail_closed(self):
        result = audit_snapshots(b"{", b'{"latest_eu_report":{}}')
        self.assertEqual(result["sources"]["US"]["status"], "INVALID_JSON")
        self.assertEqual(result["sources"]["EU"]["reports"][0]["status"], "INVALID_REPORT")
        self.assertFalse(result["trade_ready"])

    def test_pinned_fingerprint_mismatch_blocks_report(self):
        us_bytes = b'{"latest_us_reports":{"batch_1.json":{"candidates":[]}}}'
        eu_bytes = b'{"latest_eu_report":{"candidates":[]}}'
        expected = {
            "US": {"sha256": "0" * 64, "size_bytes": len(us_bytes)},
            "EU": {"sha256": hashlib.sha256(eu_bytes).hexdigest(),
                   "size_bytes": len(eu_bytes)},
        }
        result = audit_snapshots(us_bytes, eu_bytes, expected)
        self.assertEqual(result["sources"]["US"]["status"],
                         "SOURCE_FINGERPRINT_MISMATCH")
        self.assertEqual(result["sources"]["US"]["reports"], [])
        self.assertEqual(result["sources"]["EU"]["status"], "SCHEMA_AUDIT_ONLY")

    def test_pinned_fingerprint_accepts_exact_bytes(self):
        us_bytes = b'{"latest_us_reports":{"batch_1.json":{"candidates":[]}}}'
        eu_bytes = b'{"latest_eu_report":{"candidates":[]}}'
        expected = {
            market: {"sha256": hashlib.sha256(payload).hexdigest(),
                     "size_bytes": len(payload)}
            for market, payload in (("US", us_bytes), ("EU", eu_bytes))
        }
        result = audit_snapshots(us_bytes, eu_bytes, expected)
        self.assertEqual(result["sources"]["US"]["status"], "SCHEMA_AUDIT_ONLY")
        self.assertEqual(result["sources"]["EU"]["status"], "SCHEMA_AUDIT_ONLY")

    def test_bad_us_report_does_not_crash(self):
        result = audit_snapshots(b'{"latest_us_reports":{"batch_1.json":null}}',
                                 b'{"latest_eu_report":{"candidates":[]}}')
        self.assertEqual(result["sources"]["US"]["reports"][0]["status"], "INVALID_REPORT")


if __name__ == "__main__":
    unittest.main()
