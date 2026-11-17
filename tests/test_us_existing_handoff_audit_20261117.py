import unittest
from research.us_existing_handoff_audit_20261117 import audit_existing_us_handoff
T="2026-11-17T15:00:00+00:00"
def fixture():
    d={"generated_utc":T,"candidates":[{"symbol":"TEST","reference_price_usd":10}]}
    h={"generated_utc":T,"rows":[{"symbol":"TEST","discovery_lane":"FAST-MOMENTUM-RECOVERY"}]}
    r={"generated_utc":T,"rows":[{"symbol":"TEST","route_type":"EARLY-MOMENTUM-RECOVERY-VERIFY"}]}
    return d,h,r
class ExistingHandoffAuditTests(unittest.TestCase):
    def test_actual_shape_fails_closed(self):
        x=audit_existing_us_handoff(*fixture())
        self.assertFalse(x["provenance_complete"])
        self.assertIn("SOURCE_INTRADAY_TIMESTAMP_MISSING",x["rows"][0]["blocks"])
        self.assertFalse(x["notify"])
    def test_report_generated_time_is_not_source_timestamp(self):
        d,h,r=fixture()
        x=audit_existing_us_handoff(d,h,r)
        self.assertIn("DISCOVERY_OBSERVATION_TIME_MISSING",x["rows"][0]["blocks"])
    def test_complete_synthetic_metadata_still_never_trades(self):
        d,h,r=fixture()
        h["rows"][0].update({"discovery_observed_utc":T,"source_daily_last_bar_utc":T,"source_intraday_last_bar_utc":T})
        r["rows"][0].update({"pivot_origin_session_date":"2026-10-20","source_observation_utc":T})
        x=audit_existing_us_handoff(d,h,r)
        self.assertTrue(x["provenance_complete"])
        self.assertFalse(x["trade_ready"])
        self.assertFalse(x["notify"])
    def test_missing_handoff_row(self):
        d,h,r=fixture();h["rows"]=[]
        self.assertIn("HANDOFF_SYMBOL_MISSING",audit_existing_us_handoff(d,h,r)["rows"][0]["blocks"])
    def test_bad_report_timestamp(self):
        d,h,r=fixture();r["generated_utc"]="2026-11-17"
        self.assertIn("ROUTES_GENERATED_TIME_UNRESOLVED",audit_existing_us_handoff(d,h,r)["blocks"])
    def test_invalid_documents(self):
        self.assertIn("INPUT_DOCUMENT_INVALID",audit_existing_us_handoff(None,{}, {})["blocks"])
if __name__=="__main__":
    unittest.main()
