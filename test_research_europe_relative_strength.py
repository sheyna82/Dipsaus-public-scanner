"""Offline European relative strength contract tests; no external market access."""
import unittest
import hashlib,json
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
    indices["OMXH25"]["daily_label_audit"]={
        "bars_sha256":digest,
        "validation_status":"consistent_unverified","checked":21,"consistent":21,
        "inconsistent_dates":[],"identity_approved":False}
    return {"trade_ready":False,"series":stocks},{"trade_ready":False,"series":indices}
class Tests(unittest.TestCase):
    def test_forged_audit_count_is_rejected(self):
        stocks,indices=fixtures()
        audit=indices["series"]["OMXH25"]["daily_label_audit"]
        audit["consistent"]=20
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_AUDIT_BLOCKED"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_mutated_bar_digest_mismatch_blocks(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["bars"][0]["close"]+=1
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_AUDIT_HASH_MISMATCH"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_forged_consistent_audit_cannot_override_bad_bar(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["bars"][0]["t"]+=3600
        indices["series"]["OMXH25"]["daily_label_audit"]["bars_sha256"]=hashlib.sha256(json.dumps(indices["series"]["OMXH25"]["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,"OMXH25_DAILY_LABEL_AUDIT_CONTENT_MISMATCH"):
            compare(stocks,indices,IDENTITY,"2026-11-06")
    def test_duplicate_omxh25_local_session_is_blocked(self):
        stocks,indices=fixtures()
        indices["series"]["OMXH25"]["bars"][1]["t"]=indices["series"]["OMXH25"]["bars"][0]["t"]
        indices["series"]["OMXH25"]["daily_label_audit"]["bars_sha256"]=hashlib.sha256(json.dumps(indices["series"]["OMXH25"]["bars"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
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
        result=compare(stocks,indices,IDENTITY,"2026-11-06")
        self.assertAlmostEqual(result["comparisons"]["ASML.AS"]["AEX"]["relative_strength_20d_pct"],5.0)
if __name__=="__main__":unittest.main()
