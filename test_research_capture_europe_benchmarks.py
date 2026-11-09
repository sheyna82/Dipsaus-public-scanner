"""Offline benchmark capture contract tests: no external calls or trading."""
import hashlib,io,json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from research_capture_europe_benchmarks import collect,BENCHMARKS
class Response:
    status=200
    def __init__(self,body):self.body=body
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.body
def payload(symbol,currency="EUR",instrument="INDEX"):
    start=datetime(2026,4,1,12,tzinfo=timezone.utc)
    data={"chart":{"result":[{"meta":{"symbol":symbol,"currency":currency,"instrumentType":instrument,
        "shortName":"Synthetic benchmark","exchangeName":"TEST","timezone":"Europe/Paris"},
        "timestamp":[int((start+timedelta(days=i)).timestamp()) for i in range(130)],
        "indicators":{"quote":[{"close":[100+i for i in range(130)]}]}}]}}
    return json.dumps(data).encode()
class Tests(unittest.TestCase):
    def capture(self,currency="EUR",instrument="INDEX",symbol_override=None):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"capture.json"
            def fetch(req,timeout):
                import urllib.parse
                symbol=urllib.parse.unquote(req.full_url.split("/chart/")[1].split("?")[0])
                return Response(payload(symbol_override or symbol,currency,instrument))
            try:
                status=collect(path,fetch)
                return status,json.loads(path.read_text())
            except Exception:
                self.assertFalse(path.exists(),"failed capture must not create partial artifact")
                raise
    def test_success_remains_unverified(self):
        status,doc=self.capture()
        self.assertFalse(status["trade_ready"])
        self.assertFalse(doc["benchmark_identity_verified"])
        self.assertEqual(set(doc["series"]),set(BENCHMARKS))
        for key,entry in doc["series"].items():
            self.assertEqual(entry["count"],130)
            self.assertEqual(entry["provider_metadata"]["currency"],"EUR")
            self.assertEqual(entry["provider_metadata"]["instrumentType"],"INDEX")
            self.assertEqual(len(entry["source_sha256"]),64)
    def test_source_hash_matches_exact_provider_response(self):
        _,doc=self.capture()
        for name,entry in doc["series"].items():
            expected=hashlib.sha256(payload(BENCHMARKS[name])).hexdigest()
            self.assertEqual(entry["source_sha256"],expected)
            self.assertFalse(doc["benchmark_identity_verified"])
            self.assertTrue(doc["research_only"])

    def test_refuse_overwrite_of_existing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"capture.json"
            path.write_text("immutable original",encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError,"immutable_capture_exists"):
                collect(path,lambda req,timeout: self.fail("network must not be called"))
            self.assertEqual(path.read_text(encoding="utf-8"),"immutable original")

    def test_reject_wrong_currency(self):
        with self.assertRaisesRegex(ValueError,"currency_not_eur"):self.capture(currency="USD")
    def test_reject_wrong_instrument(self):
        with self.assertRaisesRegex(ValueError,"not_an_index"):self.capture(instrument="EQUITY")
    def test_reject_wrong_symbol(self):
        with self.assertRaisesRegex(ValueError,"symbol_mismatch"):self.capture(symbol_override="^WRONG")
if __name__=="__main__":unittest.main()
