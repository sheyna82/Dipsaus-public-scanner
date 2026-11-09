"""Synthetic, offline negative tests for raw provider evidence reconciliation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from test_research_capture_europe_benchmarks import Tests as CaptureTests
from research_verify_europe_benchmark_raw import verify_capture

class RawVerificationTests(unittest.TestCase):
    def setUp(self):
        # Reuse deterministic in-memory fixture; no Yahoo network calls.
        self.doc = CaptureTests().capture()[1]

    def test_positive_reconcile_does_not_approve_identity(self):
        result = verify_capture(self.doc)
        self.assertEqual(result["status"], "provider_bytes_reconciled")
        self.assertFalse(result["benchmark_identity_verified"])
        self.assertFalse(result["trade_ready"])

    def test_reject_tampered_raw_bytes(self):
        doc = copy.deepcopy(self.doc)
        doc["series"]["AEX"]["source_raw_base64"] += "AA"
        with self.assertRaisesRegex(ValueError, "BASE64_INVALID|HASH_MISMATCH"):
            verify_capture(doc)

    def test_reject_tampered_close(self):
        doc = copy.deepcopy(self.doc)
        doc["series"]["OMXH25"]["bars"][0]["close"] += 1
        with self.assertRaisesRegex(ValueError, "BARS_MISMATCH"):
            verify_capture(doc)

    def test_reject_tampered_provider_metadata(self):
        doc = copy.deepcopy(self.doc)
        doc["series"]["OMXH25"]["provider_metadata"]["exchangeName"] = "HEL"
        with self.assertRaisesRegex(ValueError, "METADATA_MISMATCH"):
            verify_capture(doc)

    def test_reject_promoted_trade_ready(self):
        doc = copy.deepcopy(self.doc)
        doc["trade_ready"] = True
        with self.assertRaisesRegex(ValueError, "GATE_INVALID"):
            verify_capture(doc)

    def test_reject_tampered_label_audit(self):
        doc = copy.deepcopy(self.doc)
        doc["series"]["OMXH25"]["daily_label_audit"]["identity_approved"] = True
        with self.assertRaisesRegex(ValueError, "LABEL_AUDIT_MISMATCH"):
            verify_capture(doc)

if __name__ == "__main__":
    unittest.main()
