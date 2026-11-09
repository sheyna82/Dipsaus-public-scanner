"""Offline benchmark capture contract tests: no external calls or trading."""
import hashlib,io,json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from research_capture_europe_benchmarks import collect,BENCHMARKS,audit_omxh25_daily_bar
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

    def test_capture_records_unapproved_label_audit(self):
        _,doc=self.capture()
        audit=doc["series"]["OMXH25"]["daily_label_audit"]
        self.assertEqual(audit["checked"],130)
        self.assertEqual(audit["consistent"],0)
        self.assertEqual(len(audit["inconsistent_dates"]),130)
        self.assertFalse(audit["identity_approved"])
        self.assertFalse(doc["benchmark_identity_verified"])

    def test_omxh25_winter_session_label(self):
        t=int(datetime(2026,11,6,8,tzinfo=timezone.utc).timestamp())
        audit=audit_omxh25_daily_bar({"t":t,"close":6221.7900390625})
        self.assertEqual(audit["session_date"],"2026-11-06")
        self.assertTrue(audit["session_open_label_consistent"])
        self.assertFalse(audit["identity_approved"])

    def test_omxh25_summer_dst_session_label(self):
        t=int(datetime(2026,7,6,7,tzinfo=timezone.utc).timestamp())
        audit=audit_omxh25_daily_bar({"t":t,"close":6200.0})
        self.assertEqual(audit["session_date"],"2026-07-06")
        self.assertTrue(audit["session_open_label_consistent"])
        self.assertFalse(audit["identity_approved"])

    def test_omxh25_wrong_label_does_not_approve(self):
        t=int(datetime(2026,11,6,16,tzinfo=timezone.utc).timestamp())
        audit=audit_omxh25_daily_bar({"t":t,"close":6221.79})
        self.assertFalse(audit["session_open_label_consistent"])
        self.assertFalse(audit["identity_approved"])

    def test_reject_wrong_currency(self):
        with self.assertRaisesRegex(ValueError,"currency_not_eur"):self.capture(currency="USD")
    def test_reject_wrong_instrument(self):
        with self.assertRaisesRegex(ValueError,"not_an_index"):self.capture(instrument="EQUITY")
    def test_reject_wrong_symbol(self):
        with self.assertRaisesRegex(ValueError,"symbol_mismatch"):self.capture(symbol_override="^WRONG")
if __name__=="__main__":unittest.main()
