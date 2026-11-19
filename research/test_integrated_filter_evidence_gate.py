"""Fail-closed regression tests for the research-only evidence gate."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from integrated_filter_evidence_gate import verify

BASE = {
    "schema": "dipsaus.prospective_filter_evaluation.v1.1",
    "status": "RESEARCH_ONLY_VERIFIED_NOT_ACTIVATED",
    "prospective_earliest_signal_date_utc": "2026-11-07",
}

class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.protocol = Path(self.tmp.name) / "protocol.json"
        self.digest = Path(self.tmp.name) / "protocol.sha256"

    def write(self, data):
        raw = json.dumps(data, sort_keys=True).encode("utf-8")
        self.protocol.write_bytes(raw)
        self.digest.write_text(hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest() + "\n", encoding="utf-8")

    def test_valid_protocol_remains_inactive(self):
        self.write(BASE)
        result = verify(self.protocol, self.digest)
        self.assertEqual(result["status"], "RESEARCH_ONLY_INTEGRITY_VERIFIED")
        self.assertFalse(result["prospective_activation"])
        self.assertFalse(result["trade_ready"])

    def test_tampered_protocol_blocked(self):
        self.write(BASE)
        self.protocol.write_text(json.dumps({**BASE, "unexpected": True}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PROTOCOL_SHA256_MISMATCH"):
            verify(self.protocol, self.digest)

    def test_whitespace_only_change_is_canonical(self):
        self.write(BASE)
        self.protocol.write_text(json.dumps(BASE, indent=4), encoding="utf-8")
        self.assertEqual(verify(self.protocol, self.digest)["status"], "RESEARCH_ONLY_INTEGRITY_VERIFIED")

    def test_wrong_schema_blocked(self):
        self.write({**BASE, "schema": "unknown"})
        with self.assertRaisesRegex(ValueError, "PROTOCOL_SCHEMA_MISMATCH"):
            verify(self.protocol, self.digest)

    def test_activated_status_blocked(self):
        self.write({**BASE, "status": "ACTIVE"})
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_PROTOCOL_STATUS"):
            verify(self.protocol, self.digest)

    def test_changed_boundary_blocked(self):
        self.write({**BASE, "prospective_earliest_signal_date_utc": "2026-11-06"})
        with self.assertRaisesRegex(ValueError, "PROSPECTIVE_BOUNDARY_MISMATCH"):
            verify(self.protocol, self.digest)

    def test_missing_digest_blocked(self):
        self.write(BASE)
        self.digest.unlink()
        with self.assertRaises(FileNotFoundError):
            verify(self.protocol, self.digest)

if __name__ == "__main__":
    unittest.main()
