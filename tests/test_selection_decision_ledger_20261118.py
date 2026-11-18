import unittest
from research.selection_decision_ledger_20261118 import audit_decision_ledger as audit

def row(**overrides):
    r={"market":"EU","symbol":"TEST","stage":"BROKER_PENDING",
       "source_observed_utc":"2026-11-18T07:00:00Z",
       "decision_observed_utc":"2026-11-18T07:05:00Z",
       "gates":{"rr_min_2":"PASS","broker_quote":"UNKNOWN"}}
    r.update(overrides)
    return r

class DecisionLedgerTests(unittest.TestCase):
    def test_pending_not_failed(self):
        x=audit([row()])
        self.assertEqual(x["counts"]["verification_pending"],1)
        self.assertEqual(x["counts"].get("failed_declared_gate",0),0)
        self.assertFalse(x["trade_ready"])
    def test_explicit_fail_is_separate(self):
        x=audit([row(gates={"rr_min_2":"FAIL","broker_quote":"UNKNOWN"})])
        self.assertEqual(x["counts"]["failed_declared_gate"],1)
        self.assertEqual(x["missing_evidence_frequency"]["broker_quote"],1)
    def test_future_source_blocked(self):
        x=audit([row(source_observed_utc="2026-11-18T08:00:00Z")])
        self.assertEqual(x["invalid_records"][0]["reason"],"PROVENANCE_INVALID")
    def test_naive_timestamp_blocked(self):
        x=audit([row(decision_observed_utc="2026-11-18T07:05:00")])
        self.assertEqual(x["invalid_records"][0]["reason"],"PROVENANCE_INVALID")
    def test_duplicate_decision_blocked(self):
        x=audit([row(),row()])
        self.assertEqual(x["invalid_records"][0]["reason"],"DUPLICATE_DECISION")
    def test_distinct_stages_allowed(self):
        x=audit([row(),row(stage="TECHNICAL_REVIEW")])
        self.assertEqual(x["counts"]["valid_decisions"],2)
    def test_invalid_gate_not_accepted(self):
        x=audit([row(gates={"unknown_gate":"PASS"})])
        self.assertEqual(x["invalid_records"][0]["reason"],"GATES_INVALID")
    def test_missing_input_blocked(self):
        self.assertEqual(audit(None)["status"],"INVALID_INPUT")
    def test_self_reported_all_pass_never_authorizes(self):
        x=audit([row(gates={})])
        self.assertFalse(x["trade_ready"])
        self.assertFalse(x["automatic_orders"])
if __name__=="__main__":
    unittest.main()
