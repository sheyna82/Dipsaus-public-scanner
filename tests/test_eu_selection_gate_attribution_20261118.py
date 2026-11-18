import unittest
from research.eu_selection_gate_attribution_20261118 import audit_eu_gate_attribution as audit

class EUSelectionAttributionTests(unittest.TestCase):
    def test_missing_broker_evidence_not_technical_failure(self):
        x=audit([{"id":"A","gates":{"technical_structure":"PASS","rr_min_2":"PASS","broker_quote":"UNKNOWN"}}])
        self.assertEqual(x["counts"]["pending_verification"],1)
        self.assertEqual(x["counts"].get("proven_gate_failure",0),0)
    def test_failed_rr_distinct_from_missing_broker(self):
        x=audit([{"id":"A","gates":{"rr_min_2":"FAIL","broker_quote":"UNKNOWN"}}])
        self.assertEqual(x["first_failure_by_declared_gate_order"]["rr_min_2"],1)
        self.assertEqual(x["missing_evidence_frequency"]["broker_quote"],1)
    def test_multiple_failures_not_double_count_candidates(self):
        x=audit([{"id":"A","gates":{"rr_min_2":"FAIL","net_profit_min_150":"FAIL"}}])
        self.assertEqual(x["counts"]["proven_gate_failure"],1)
        self.assertEqual(len(x["all_failure_frequency"]),2)
    def test_all_pass_still_not_trade_ready(self):
        keys=("technical_structure","rr_min_2","net_profit_min_150","broker_quote","event_clearance","portfolio_fit")
        x=audit([{"id":"A","gates":{k:"PASS" for k in keys}}])
        self.assertEqual(x["counts"]["all_declared_gates_passed_unverified"],1)
        self.assertFalse(x["trade_ready"])
    def test_duplicate_id_invalid(self):
        x=audit([{"id":"A","gates":{}},{"id":"A","gates":{}}])
        self.assertEqual(x["invalid_row_indices"],[1])
    def test_unknown_gate_invalid(self):
        x=audit([{"id":"A","gates":{"invented":"PASS"}}])
        self.assertEqual(x["invalid_row_indices"],[0])
    def test_missing_input_fails_closed(self):
        self.assertEqual(audit(None)["status"],"INVALID_INPUT")
if __name__=="__main__":
    unittest.main()
