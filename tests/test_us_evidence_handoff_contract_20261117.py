import unittest
from research.us_evidence_handoff_contract_20261117 import carry_evidence,FIELDS
D={"symbol":"TEST","discovery_observed_utc":"2026-11-17T15:00:00+00:00",
   "source_daily_last_bar_utc":"2026-11-17T14:00:00+00:00",
   "source_intraday_last_bar_utc":"2026-11-17T14:59:00+00:00",
   "pivot_origin_session_date":"2026-10-20",
   "exchange_session_date":"2026-11-17"}
class EvidenceHandoffContractTests(unittest.TestCase):
    def test_complete_evidence_carried_without_authorization(self):
        r=carry_evidence(dict(D),{"symbol":"TEST"},symbol="TEST")
        self.assertTrue(r["provenance_fields_complete"])
        self.assertEqual(len(r["evidence"]),len(FIELDS))
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["notify"])
    def test_missing_source_not_filled_from_handoff(self):
        d=dict(D);d.pop("source_intraday_last_bar_utc")
        h={"symbol":"TEST","source_intraday_last_bar_utc":"2026-11-17T14:59:00+00:00"}
        r=carry_evidence(d,h,symbol="TEST")
        self.assertIn("SOURCE_INTRADAY_LAST_BAR_UTC_SOURCE_MISSING",r["blocks"])
    def test_conflicting_handoff_rejected(self):
        h={"symbol":"TEST","exchange_session_date":"2026-11-16"}
        r=carry_evidence(dict(D),h,symbol="TEST")
        self.assertIn("EXCHANGE_SESSION_DATE_HANDOFF_CONFLICT",r["blocks"])
    def test_symbol_mismatch(self):
        r=carry_evidence(dict(D),{"symbol":"OTHER"},symbol="TEST")
        self.assertIn("SYMBOL_MISMATCH",r["blocks"])
    def test_naive_timestamp_rejected(self):
        d=dict(D);d["discovery_observed_utc"]="2026-11-17T15:00:00"
        self.assertIn("DISCOVERY_OBSERVED_UTC_SOURCE_INVALID",carry_evidence(d,{"symbol":"TEST"},symbol="TEST")["blocks"])
    def test_invalid_input(self):
        self.assertIn("INPUT_INVALID",carry_evidence(None,{},symbol="TEST")["blocks"])
if __name__=="__main__":
    unittest.main()
