import unittest
from research.us_handoff_ledger_adapter_20261118 import audit_us_handoff_ledger_readiness as audit

class HandoffLedgerAdapterTests(unittest.TestCase):
    def test_generated_timestamp_does_not_fill_source_time(self):
        r=audit({"generated_utc":"2026-11-18T07:00:00Z","rows":[{"symbol":"ABC","execution_blocks":["BROKER-BID-ASK-NOT-VERIFIED"]}]})
        self.assertIn("SOURCE_DAILY_LAST_BAR_UTC_MISSING",r["rows"][0]["blocks"])
        self.assertIn("DECISION_OBSERVED_UTC_MISSING",r["rows"][0]["blocks"])
        self.assertFalse(r["trade_ready"])
    def test_promoted_does_not_mean_structure_confirmed(self):
        r=audit({"rows":[{"symbol":"ABC","auto_promoted":True,"structure_quality_pass":False}]})
        self.assertTrue(r["rows"][0]["research_promotion"])
        self.assertFalse(r["rows"][0]["structure_confirmed"])
    def test_unverified_execution_claim_flagged(self):
        r=audit({"rows":[{"symbol":"ABC","execution_ready":True}]})
        self.assertIn("UNVERIFIED_EXECUTION_READY_CLAIM",r["rows"][0]["blocks"])
    def test_invalid_handoff_blocked(self):
        self.assertEqual(audit({})["blocks"],["HANDOFF_ROWS_INVALID"])
    def test_invalid_symbol_visible(self):
        r=audit({"rows":[{"symbol":""}]})
        self.assertEqual(r["rows"][0]["status"],"INVALID_ROW")
    def test_complete_fields_still_not_authorized(self):
        row={"symbol":"ABC","gates":{},
             "discovery_observed_utc":"2026-11-18T07:00:00Z",
             "source_daily_last_bar_utc":"2026-11-18T07:00:00Z",
             "source_intraday_last_bar_utc":"2026-11-18T07:00:00Z",
             "decision_observed_utc":"2026-11-18T07:05:00Z"}
        r=audit({"rows":[row]})
        self.assertEqual(r["rows"][0]["status"],"LEDGER_INPUT_REQUIRES_VALIDATION")
        self.assertFalse(r["automatic_orders"])
if __name__=="__main__":
    unittest.main()
