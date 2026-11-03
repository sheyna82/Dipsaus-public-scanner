"""Tests for multi-artifact offline collection."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from research_finnhub_artifact_collection import build_artifact_collection

class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
    def artifact(self, symbol, second, name, price=100):
        raw = json.dumps({"c":price,"t":1793737456}).encode()
        record = {"schema":"dipsaus_research_source_observation_v1",
            "provider":"Finnhub","endpoint":"/api/v1/quote","symbol_requested":symbol,
            "request_started_utc":f"2026-11-03T20:24:{second:02d}+00:00",
            "response_finished_utc":f"2026-11-03T20:25:{second:02d}+00:00",
            "raw_response_hex":raw.hex(),"source_bytes":len(raw),
            "source_sha256":hashlib.sha256(raw).hexdigest(),
            "source_timestamp_claim_unverified":1793737456,
            "external_receipt_verified":False,"provider_identity_independently_verified":False,
            "prospective_signal_proven":False,"research_only":True,"trade_ready":False}
        path=self.root/name
        with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("source-observation.json",json.dumps(record))
        return (path,hashlib.sha256(path.read_bytes()).hexdigest())
    def test_two_observations_deterministic(self):
        a=self.artifact("AMD",10,"a.zip")
        b=self.artifact("COHU",20,"b.zip")
        x=build_artifact_collection([a,b])
        self.assertEqual(x,build_artifact_collection([b,a]))
        self.assertEqual(x["count"],2)
        self.assertEqual(len(x["artifact_receipts"]),2)
        self.assertFalse(x["trade_ready"])
    def test_duplicate_artifact_rejected(self):
        a=self.artifact("AMD",10,"a.zip")
        with self.assertRaisesRegex(ValueError,"duplicate_artifact"):
            build_artifact_collection([a,a])
    def test_conflicting_window_rejected(self):
        a=self.artifact("AMD",10,"a.zip",100)
        b=self.artifact("AMD",10,"b.zip",101)
        with self.assertRaisesRegex(ValueError,"duplicate_observation_window"):
            build_artifact_collection([a,b])
    def test_invalid_digest_rejected(self):
        a=self.artifact("AMD",10,"a.zip")
        with self.assertRaisesRegex(ValueError,"zip_hash_mismatch"):
            build_artifact_collection([(a[0],"0"*64)])
    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError,"artifact_inputs_required"):
            build_artifact_collection([])

if __name__=="__main__": unittest.main()
