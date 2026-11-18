import unittest
from research.us_selection_effectiveness_audit_20261118 import audit_selection_handoff

class SelectionAuditTests(unittest.TestCase):
    def test_stage_counts_are_distinct(self):
        rows=[{"symbol":"AAA","discovery_lane":"FAST-MOMENTUM-RECOVERY","auto_promoted":True,
               "structure_quality_pass":False,"execution_ready":False,
               "execution_blocks":["R-R-2X-NOT-VERIFIED","BROKER-BID-ASK-NOT-VERIFIED"]},
              {"symbol":"BBB","discovery_lane":"DEEP-RECOVERY","auto_promoted":False,
               "execution_ready":False,"execution_blocks":["BROKER-BID-ASK-NOT-VERIFIED"]}]
        result=audit_selection_handoff({"rows":rows})
        self.assertEqual(result["counts"]["discovered_handoff_rows"],2)
        self.assertEqual(result["counts"]["prealert_promoted_rows"],1)
        self.assertEqual(result["counts"].get("intraday_structure_confirmed_rows",0),0)
        self.assertEqual(result["execution_block_frequency"]["BROKER-BID-ASK-NOT-VERIFIED"],2)
        self.assertFalse(result["trade_ready"])
    def test_duplicate_block_per_row_not_double_counted(self):
        r=audit_selection_handoff({"rows":[{"symbol":"A","execution_blocks":["X","X"]}]})
        self.assertEqual(r["execution_block_frequency"]["X"],1)
    def test_missing_blocks_not_treated_as_clearance(self):
        r=audit_selection_handoff({"rows":[{"symbol":"A"}]})
        self.assertEqual(r["execution_block_frequency"]["EXECUTION_BLOCKS_MISSING_OR_INVALID"],1)
    def test_duplicate_symbol_is_visible(self):
        r=audit_selection_handoff({"rows":[{"symbol":"A"},{"symbol":"A"}]})
        self.assertEqual(r["duplicate_symbol_count"],1)
    def test_invalid_rows_counted(self):
        r=audit_selection_handoff({"rows":[None,{"symbol":""}]})
        self.assertEqual(r["invalid_row_count"],2)
    def test_unverified_execution_claim_is_flagged(self):
        r=audit_selection_handoff({"rows":[{"symbol":"A","execution_ready":True}]})
        self.assertIn("UNVERIFIED_EXECUTION_READY_CLAIMS",r["issues"])
        self.assertFalse(r["trade_ready"])
    def test_invalid_document_blocks(self):
        r=audit_selection_handoff({})
        self.assertEqual(r["status"],"INVALID_INPUT")
        self.assertFalse(r["notify"])
if __name__=="__main__":
    unittest.main()
