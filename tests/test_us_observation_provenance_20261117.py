import unittest
from datetime import datetime, timezone, timedelta
from research.us_observation_provenance_20261117 import review_provenance

NOW = datetime(2026,11,17,16,0,tzinfo=timezone.utc)
def fixture():
    return {
        "discovery_observed_utc":(NOW-timedelta(minutes=2)).isoformat(),
        "source_daily_last_bar_utc":(NOW-timedelta(hours=2)).isoformat(),
        "source_intraday_last_bar_utc":(NOW-timedelta(minutes=3)).isoformat(),
        "route_generated_utc":(NOW-timedelta(minutes=1)).isoformat(),
        "quote_observed_utc":(NOW-timedelta(seconds=20)).isoformat(),
        "exchange_session_date":"2026-11-17",
        "pivot_origin_session_date":"2026-10-20",
    }
class ProvenanceTests(unittest.TestCase):
    def check(self,r):
        return review_provenance(r,now=NOW)
    def test_old_pivot_is_not_stale_observation(self):
        result=self.check(fixture())
        self.assertTrue(result["temporal_evidence_consistent"])
        self.assertFalse(result["trade_ready"])
        self.assertIn("PIVOT_CORPORATE_ACTION_VALIDITY_UNVERIFIED",result["blocks"])
    def test_missing_intraday_origin(self):
        r=fixture();r.pop("source_intraday_last_bar_utc")
        self.assertIn("SOURCE_INTRADAY_LAST_BAR_UTC_UNRESOLVED",self.check(r)["blocks"])
    def test_stale_intraday(self):
        r=fixture();r["source_intraday_last_bar_utc"]=(NOW-timedelta(hours=1)).isoformat()
        self.assertIn("INTRADAY_SOURCE_STALE_OR_FUTURE",self.check(r)["blocks"])
    def test_discovery_after_route(self):
        r=fixture();r["route_generated_utc"]=(NOW-timedelta(minutes=4)).isoformat()
        self.assertIn("ROUTE_BEFORE_DISCOVERY",self.check(r)["blocks"])
    def test_pivot_from_future(self):
        r=fixture();r["pivot_origin_session_date"]="2026-11-18"
        self.assertIn("PIVOT_FROM_FUTURE_SESSION",self.check(r)["blocks"])
    def test_quote_session_mismatch(self):
        r=fixture();r["exchange_session_date"]="2026-11-16"
        self.assertIn("QUOTE_SESSION_MISMATCH",self.check(r)["blocks"])
    def test_missing_daily_origin(self):
        r=fixture();r["source_daily_last_bar_utc"]=None
        self.assertIn("SOURCE_DAILY_LAST_BAR_UTC_UNRESOLVED",self.check(r)["blocks"])
    def test_future_intraday_bar(self):
        r=fixture();r["source_intraday_last_bar_utc"]=(NOW-timedelta(minutes=1)).isoformat()
        self.assertIn("INTRADAY_BAR_AFTER_DISCOVERY",self.check(r)["blocks"])
    def test_bad_date_format(self):
        r=fixture();r["pivot_origin_session_date"]="17-11-2026"
        self.assertIn("PIVOT_ORIGIN_DATE_UNRESOLVED",self.check(r)["blocks"])
if __name__=="__main__":
    unittest.main()
