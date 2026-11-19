"""Integration readiness tests: no false green before frozen evidence exists."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from integrated_evidence_readiness import readiness

BASE = {"schema": "dipsaus.research_evidence_manifest.v1",
        "research_only": True, "trade_ready": False,
        "protocol_embedded": False}

class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        p = Path(self.temp.name)
        self.manifest = p / "manifest.json"
        self.protocol = p / "protocol.json"
        self.digest = p / "protocol.sha256"

    def set_manifest(self, **updates):
        self.manifest.write_text(json.dumps({**BASE, **updates}), encoding="utf-8")

    def test_unimported_protocol_blocks(self):
        self.set_manifest()
        self.assertEqual(readiness(self.manifest, self.protocol, self.digest)["status"],
                         "BLOCKED_PROTOCOL_NOT_IMPORTED")

    def test_missing_files_block(self):
        self.set_manifest(protocol_embedded=True)
        self.assertEqual(readiness(self.manifest, self.protocol, self.digest)["status"],
                         "BLOCKED_PROTOCOL_FILES_MISSING")

    def test_wrong_manifest_schema_rejected(self):
        self.set_manifest(schema="unknown")
        with self.assertRaisesRegex(ValueError, "INVALID_MANIFEST_SCHEMA"):
            readiness(self.manifest, self.protocol, self.digest)

    def test_trade_ready_flag_rejected(self):
        self.set_manifest(trade_ready=True)
        with self.assertRaisesRegex(ValueError, "UNSAFE_MANIFEST_STATUS"):
            readiness(self.manifest, self.protocol, self.digest)

    def test_matching_protocol_is_integrity_only(self):
        payload = {"schema": "dipsaus.prospective_filter_evaluation.v1.1",
                   "status": "RESEARCH_ONLY_VERIFIED_NOT_ACTIVATED",
                   "prospective_earliest_signal_date_utc": "2026-11-07"}
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        digest = hashlib.sha256(raw).hexdigest()
        self.protocol.write_bytes(raw)
        self.digest.write_text(digest + "\n", encoding="utf-8")
        self.set_manifest(protocol_embedded=True, protocol_sha256_canonical_json=digest)
        result = readiness(self.manifest, self.protocol, self.digest)
        self.assertEqual(result["status"], "RESEARCH_EVIDENCE_INTEGRITY_VERIFIED")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["prospective_activation"])

    def test_manifest_hash_mismatch_rejected(self):
        payload = {"schema": "dipsaus.prospective_filter_evaluation.v1.1",
                   "status": "RESEARCH_ONLY_VERIFIED_NOT_ACTIVATED",
                   "prospective_earliest_signal_date_utc": "2026-11-07"}
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.protocol.write_bytes(raw)
        self.digest.write_text(hashlib.sha256(raw).hexdigest(), encoding="utf-8")
        self.set_manifest(protocol_embedded=True, protocol_sha256_canonical_json="0"*64)
        with self.assertRaisesRegex(ValueError, "MANIFEST_PROTOCOL_HASH_MISMATCH"):
            readiness(self.manifest, self.protocol, self.digest)

if __name__ == "__main__":
    unittest.main()
