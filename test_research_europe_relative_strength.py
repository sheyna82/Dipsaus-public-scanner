"""Offline European relative strength contract tests; no external market access."""
import unittest
from datetime import datetime,timedelta,timezone
from research_europe_relative_strength import compare
IDENTITY={k:True for k in ("AEX","DAX_PRICE","OMXH25","STOXX600_PRICE")}
def bars(start,finish):
    base=datetime(2026,10,5,12,tzinfo=timezone.utc)
    return [{"t":int((base+timedelta(days=i)).timestamp()),"close":start+(finish-start)*i/20}
            for i in range(21)]
def fixtures():
    stocks={k:{"bars":bars(100,110)} for k in ("ASML.AS","IFX.DE","NOKIA.HE","RHM.DE")}
    indices={k:{"bars":bars(100,105)} for k in IDENTITY}
    return {"trade_ready":False,"series":stocks},{"trade_ready":False,"series":indices}
class Tests(unittest.TestCase):
    def test_missing_evidence_blocks(self):
        with self.assertRaisesRegex(ValueError,"BENCHMARK_IDENTITY_UNVERIFIED"):
            compare({"trade_ready":False},{"trade_ready":False},{})
    def test_partial_evidence_blocks(self):
        with self.assertRaisesRegex(ValueError,"BENCHMARK_IDENTITY_UNVERIFIED"):
            compare({"trade_ready":False},{"trade_ready":False},{"AEX":True})
    def test_trade_ready_source_blocks(self):
        with self.assertRaisesRegex(ValueError,"RESEARCH_ONLY_REQUIRED"):
            compare({"trade_ready":True},{"trade_ready":False},{})
    def test_aligned_twenty_session_relative_return(self):
        stocks,indices=fixtures()
        result=compare(stocks,indices,IDENTITY)
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
            compare(stocks,indices,IDENTITY)
    def test_incomplete_current_session_excluded(self):
        stocks,indices=fixtures()
        for v in stocks["series"].values():v["bars"].append({"t":int(datetime(2026,11,9,12,tzinfo=timezone.utc).timestamp()),"close":9999})
        for v in indices["series"].values():v["bars"].append({"t":int(datetime(2026,11,9,12,tzinfo=timezone.utc).timestamp()),"close":1})
        result=compare(stocks,indices,IDENTITY)
        self.assertAlmostEqual(result["comparisons"]["ASML.AS"]["AEX"]["relative_strength_20d_pct"],5.0)
if __name__=="__main__":unittest.main()
