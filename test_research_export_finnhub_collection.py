"""Write-once archive export regression tests."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from research_export_finnhub_collection import export_collection

class ExportTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        raw=json.dumps({"c":100,"t":1793737456}).encode()
        record={"schema":"dipsaus_research_source_observation_v1",
            "provider":"Finnhub","endpoint":"/api/v1/quote","symbol_requested":"AMD",
            "request_started_utc":"2026-11-03T20:24:14+00:00",
            "response_finished_utc":"2026-11-03T20:24:15+00:00",
            "raw_response_hex":raw.hex(),"source_bytes":len(raw),
            "source_sha256":hashlib.sha256(raw).hexdigest(),
            "source_timestamp_claim_unverified":1793737456,
            "external_receipt_verified":False,"provider_identity_independently_verified":False,
            "prospective_signal_proven":False,"research_only":True,"trade_ready":False}
        self.archive=self.root/"sample.zip"
        with zipfile.ZipFile(self.archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("source-observation.json",json.dumps(record))
        self.pair=(self.archive,hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.output=self.root/"collection.json"
    def test_export_and_parse(self):
        result=export_collection(self.output,[self.pair])
        self.assertEqual(result["count"],1)
        self.assertEqual(json.loads(self.output.read_text()),result)
        self.assertFalse(result["trade_ready"])
    def test_existing_file_never_overwritten(self):
        self.output.write_text("keep")
        with self.assertRaises(FileExistsError):
            export_collection(self.output,[self.pair])
        self.assertEqual(self.output.read_text(),"keep")
    def test_invalid_digest_creates_no_output(self):
        with self.assertRaisesRegex(ValueError,"zip_hash_mismatch"):
            export_collection(self.output,[(self.archive,"0"*64)])
        self.assertFalse(self.output.exists())
    def test_empty_collection_creates_no_output(self):
        with self.assertRaisesRegex(ValueError,"artifact_inputs_required"):
            export_collection(self.output,[])
        self.assertFalse(self.output.exists())

if __name__=="__main__": unittest.main()
