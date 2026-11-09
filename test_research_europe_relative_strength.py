"""Offline European relative strength contract tests; no external market access."""
import unittest
import hashlib,json,base64
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from research_europe_relative_strength import compare
IDENTITY={k:True for k in ("AEX","DAX_PRICE","OMXH25","STOXX600_PRICE")}
def bars(start,finish):
    base=datetime(2026,10,5,12,tzinfo=timezone.utc)
    return [{"t":int((base+timedelta(days=i)).timestamp()),"close":start+(finish-start)*i/20}
            for i in range(21)]
def fixtures():
    stocks={k:{"bars":bars(100,110)} for k in ("ASML.AS","IFX.DE","NOKIA.HE","RHM.DE")}
    indices={k:{"bars":bars(100,105)} for k in IDENTITY}
    # Use actual Helsinki 10:00 session labels across DST changes.
    for bar in indices["OMXH25"]["bars"]:
        day=datetime.fromtimestamp(bar["t"],timezone.utc).date()
        bar["t"]=int(datetime(day.year,day.month,day.day,10,tzinfo=ZoneInfo("Europe/Helsinki")).timestamp())
    digest=hashlib.sha256(json.dumps(indices["OMXH25"]["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    indices["OMXH25"]["provider_metadata"]={"symbol":"^OMXH25","currency":"EUR","instrumentType":"INDEX","longName":"OMX Helsinki 25"}
    omx_bars=indices["OMXH25"]["bars"]
    source={"chart":{"result":[{"meta":dict(indices["OMXH25"]["provider_metadata"]),
             "timestamp":[b["t"] for b in omx_bars],
             "indicators":{"quote":[{"close":[b["close"] for b in omx_bars]}]}}]}}
    raw=json.dumps(source,sort_keys=True,separators=(",",":")).encode()
    indices["OMXH25"]["source_raw_base64"]=base64.b64encode(raw).decode("ascii")
    indices["OMXH25"]["source_sha256"]=hashlib.sha256(raw).hexdigest()
    indices["OMXH25"]["daily_label_audit"]={
        "bars_sha256":digest,
        "validation_status":"consistent_unverified","checked":21,"consistent":21,
        "inconsistent_dates":[],"identity_approved":False}
    return {"trade_ready":False,"series":stocks},{"trade_ready":False,"series":indices}
def sync_raw_omx(omx):
    payload=json.loads(base64.b64decode(omx["source_raw_base64"]))
    payload["chart"]["result"][0]["timestamp"]=[b["t"] for b in omx["bars"]]
    payload["chart"]["result"][0]["indicators"]["quote"][0]["close"]=[b["close"] for b in omx["bars"]]
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    omx["source_raw_base64"]=base64.b64encode(raw).decode("ascii")
    omx["source_sha256"]=hashlib.sha256(raw).hexdigest()
class Tests(unittest.TestCase):
    def test_modified_provider_metadata_blocks_even_when_plausible(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["provider_metadata"]["longName"]="OMX Helsinki 25 alternative"
        with self.assertRaisesRegex(ValueError,"OMXH25_RAW_SOURCE_PARSE_FAILED"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_modified_raw_provider_metadata_blocks(self):
        stocks,indices=fixtures()
        omx=indices["series"]["OMXH25"]
        payload=json.loads(base64.b64decode(omx["source_raw_base64"]))
        payload["chart"]["result"][0]["meta"]["exchangeName"]="FAKE"
        raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
        omx["source_raw_base64"]=base64.b64encode(raw).decode("ascii")
        omx["source_sha256"]=hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError,"OMXH25_RAW_SOURCE_PARSE_FAILED"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_raw_source_bars_mismatch_blocks_even_with_updated_bar_hash(self):
        stocks,indices=fixtures()
        omx=indices["series"]["OMXH25"]
        omx["bars"][0]["close"]+=1
        omx["daily_label_audit"]["bars_sha256"]=hashlib.sha256(json.dumps(omx["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,"OMXH25_RAW_SOURCE_BARS_MISMATCH"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_missing_raw_source_blocks(self):
        stocks,indices=fixtures()
        del indices["series"]["OMXH25"]["source_raw_base64"]
        with self.assertRaisesRegex(ValueError,"OMXH25_RAW_SOURCE_MISSING"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_tampered_raw_source_blocks(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["source_raw_base64"]=base64.b64encode(b"tampered").decode("ascii")
        with self.assertRaisesRegex(ValueError,"OMXH25_RAW_SOURCE_HASH_MISMATCH"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_missing_source_digest_blocks(self):
        stocks,indices=fixtures()
        del indices["series"]["OMXH25"]["source_sha256"]
        with self.assertRaisesRegex(ValueError,"OMXH25_SOURCE_DIGEST_MISSING"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_wrong_provider_metadata_blocks(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["provider_metadata"]["instrumentType"]="EQUITY"
        with self.assertRaisesRegex(ValueError,"OMXH25_PROVIDER_METADATA_UNVERIFIED"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_forged_status_counts_and_hash_cannot_hide_wrong_timestamp(self):
        stocks,indices=fixtures()
        omx=indices["series"]["OMXH25"]
        omx["bars"][3]["t"]+=3600
        audit=omx["daily_label_audit"]
        audit.update({"validation_status":"consistent_unverified",
                      "checked":len(omx["bars"]),"consistent":len(omx["bars"]),
                      "inconsistent_dates":[],"identity_approved":False})
        audit["bars_sha256"]=hashlib.sha256(json.dumps(omx["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        sync_raw_omx(omx)
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_AUDIT_CONTENT_MISMATCH"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_forged_status_counts_and_hash_cannot_hide_duplicate_day(self):
        stocks,indices=fixtures()
        omx=indices["series"]["OMXH25"]
        omx["bars"][4]["t"]=omx["bars"][3]["t"]
        audit=omx["daily_label_audit"]
        audit.update({"validation_status":"consistent_unverified",
                      "checked":len(omx["bars"]),"consistent":len(omx["bars"]),
                      "inconsistent_dates":[],"identity_approved":False})
        audit["bars_sha256"]=hashlib.sha256(json.dumps(omx["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        sync_raw_omx(omx)
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_RECOMPUTE_BLOCKED"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_forged_audit_count_is_rejected(self):
        stocks,indices=fixtures()
        audit=indices["series"]["OMXH25"]["daily_label_audit"]
        audit["consistent"]=20
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_AUDIT_BLOCKED"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_mutated_bar_digest_mismatch_blocks(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["bars"][0]["close"]+=1
        sync_raw_omx(indices["series"]["OMXH25"])
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_AUDIT_HASH_MISMATCH"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_forged_consistent_audit_cannot_override_bad_bar(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["bars"][0]["t"]+=3600
        indices["series"]["OMXH25"]["daily_label_audit"]["bars_sha256"]=hashlib.sha256(json.dumps(indices["series"]["OMXH25"]["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        sync_raw_omx(indices["series"]["OMXH25"])
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_AUDIT_CONTENT_MISMATCH"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_duplicate_omxh25_local_session_is_blocked(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["bars"][1]["t"]=indices["series"]["OMXH25"]["bars"][0]["t"]
        indices["series"]["OMXH25"]["daily_label_audit"]["bars_sha256"]=hashlib.sha256(json.dumps(indices["series"]["OMXH25"]["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        sync_raw_omx(indices["series"]["OMXH25"])
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_RECOMPUTE_BLOCKED"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_missing_omxh25_audit_vetoes_comparison(self):
        stocks,indices=fixtures()
        del indices["series"]["OMXH25"]["daily_label_audit"]
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_AUDIT_MISSING"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_inconsistent_omxh25_audit_vetoes_comparison(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["daily_label_audit"]={
            "validation_status":"blocked","checked":21,"consistent":20,
            "inconsistent_dates":["2026-10-06"],"identity_approved":False}
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_AUDIT_BLOCKED"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_consistent_unverified_audit_does_not_claim_approval(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["daily_label_audit"]={
            "validation_status":"consistent_unverified","checked":21,"consistent":21,
            "inconsistent_dates":[],"identity_approved":False,
            "bars_sha256":hashlib.sha256(json.dumps(indices["series"]["OMXH25"]["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()}
        result=compare(stocks,indices,IDENTITY,"2026-11-06")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["selection_thresholds_approved"])
    def test_missing_evidence_blocks(self):
        with self.assertRaisesRegex(ValueError,"BENCHMARK_IDENTITY_UNVERIFIED"):
            compare({"trade_ready":False},{"trade_ready":False},{},"2026-11-06")
    def test_partial_evidence_blocks(self):
        with self.assertRaisesRegex(ValueError,"BENCHMARK_IDENTITY_UNVERIFIED"):
            compare({"trade_ready":False},{"trade_ready":False},{"AEX":True},"2026-11-06")
    def test_trade_ready_source_blocks(self):
        with self.assertRaisesRegex(ValueError,"RESEARCH_ONLY_REQUIRED"):
            compare({"trade_ready":True},{"trade_ready":False},{},"2026-11-06")
    def test_aligned_twenty_session_relative_return(self):
        stocks,indices=fixtures()
        result=compare(stocks,indices,IDENTITY,"2026-11-06")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["selection_thresholds_approved"])
        self.assertEqual(len(result["comparisons"]),4)
        for by_benchmark in result["comparisons"].values():
            self.assertEqual(len(by_benchmark),2)
            for comparison in by_benchmark.values():
                self.assertAlmostEqual(comparison["relative_strength_20d_pct"],5.0,places=10)
                self.assertEqual(comparison["matched_sessions"],21)
    def test_missing_benchmark_days_blocks(self):
        stocks,indices=fixtures()
        indices["series"]["AEX"]["bars"]=indices["series"]["AEX"]["bars"][1:]
        with self.assertRaisesRegex(ValueError,"INSUFFICIENT_MATCHED_DAYS"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_invalid_cutoff_blocks(self):
        stocks,indices=fixtures()
        with self.assertRaisesRegex(ValueError,"INVALID_COMPLETE_SESSION_CUTOFF"):
            compare(stocks,indices,IDENTITY,"2026-99-99")
    def test_incomplete_current_session_excluded(self):
        stocks,indices=fixtures()
        for v in stocks["series"].values():v["bars"].append({"t":int(datetime(2026,11,9,12,tzinfo=timezone.utc).timestamp()),"close":9999})
        for name,v in indices["series"].items():
            t=datetime(2026,11,9,10,tzinfo=ZoneInfo("Europe/Helsinki")) if name=="OMXH25" else datetime(2026,11,9,12,tzinfo=timezone.utc)
            v["bars"].append({"t":int(t.timestamp()),"close":1})
        # Synthetic audit fixture must cover the appended (incomplete) observation.
        audit=indices["series"]["OMXH25"]["daily_label_audit"]
        audit["checked"]=22
        audit["consistent"]=22
        audit["bars_sha256"]=hashlib.sha256(json.dumps(indices["series"]["OMXH25"]["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        sync_raw_omx(indices["series"]["OMXH25"])
        result=compare(stocks,indices,IDENTITY,"2026-11-06")
        self.assertAlmostEqual(result["comparisons"]["ASML.AS"]["AEX"]["relative_strength_20d_pct"],5.0)
if __name__=="__main__":unittest.main()
