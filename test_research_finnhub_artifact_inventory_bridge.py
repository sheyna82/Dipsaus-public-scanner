"""Negative and positive tests for bounded offline Finnhub ZIP bridge."""
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from research_finnhub_artifact_inventory_bridge import inventory_from_artifact

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "artifact.zip"
        raw = json.dumps({"c":100,"t":1793737456}, separators=(",",":")).encode()
        self.record = {
            "schema":"dipsaus_research_source_observation_v1",
            "provider":"Finnhub","endpoint":"/api/v1/quote","symbol_requested":"AMD",
            "request_started_utc":"2026-11-03T20:24:14+00:00",
            "response_finished_utc":"2026-11-03T20:24:15+00:00",
            "raw_response_hex":raw.hex(),"source_bytes":len(raw),
            "source_sha256":hashlib.sha256(raw).hexdigest(),
            "source_timestamp_claim_unverified":1793737456,
            "external_receipt_verified":False,
            "provider_identity_independently_verified":False,
            "prospective_signal_proven":False,
            "research_only":True,"trade_ready":False}
    def write(self, members=None):
        if members is None:
            members={"source-observation.json":json.dumps(self.record).encode()}
        with zipfile.ZipFile(self.path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for name,data in members.items(): z.writestr(name,data)
        return hashlib.sha256(self.path.read_bytes()).hexdigest()
    def test_valid(self):
        digest=self.write()
        result=inventory_from_artifact(self.path,expected_zip_sha256=digest)
        self.assertEqual(result["inventory"]["count"],1)
        self.assertFalse(result["trade_ready"])
    def test_wrong_digest(self):
        self.write()
        with self.assertRaisesRegex(ValueError,"zip_hash_mismatch"):
            inventory_from_artifact(self.path,expected_zip_sha256="0"*64)
    def test_path_traversal(self):
        digest=self.write({"../source-observation.json":b"{}"})
        with self.assertRaisesRegex(ValueError,"unexpected_zip_members"):
            inventory_from_artifact(self.path,expected_zip_sha256=digest)
    def test_extra_member(self):
        digest=self.write({"source-observation.json":b"{}","extra":b"x"})
        with self.assertRaisesRegex(ValueError,"unexpected_zip_members"):
            inventory_from_artifact(self.path,expected_zip_sha256=digest)
    def test_oversized_member(self):
        digest=self.write({"source-observation.json":b"x"*9000})
        with self.assertRaisesRegex(ValueError,"unsafe_zip_member"):
            inventory_from_artifact(self.path,expected_zip_sha256=digest)
    def test_tampered_source(self):
        self.record["source_sha256"]="0"*64
        digest=self.write()
        with self.assertRaisesRegex(ValueError,"source_hash_mismatch"):
            inventory_from_artifact(self.path,expected_zip_sha256=digest)
    def test_missing_archive(self):
        with self.assertRaisesRegex(ValueError,"zip_size_invalid"):
            inventory_from_artifact(self.path,expected_zip_sha256="0"*64)
    def test_bad_zip(self):
        self.path.write_bytes(b"not a zip")
        digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,"invalid_zip_archive"):
            inventory_from_artifact(self.path,expected_zip_sha256=digest)

if __name__=="__main__": unittest.main()
