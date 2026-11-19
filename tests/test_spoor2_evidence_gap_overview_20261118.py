import unittest
from research.spoor2_evidence_gap_overview_20261118 import summarize_spoor2_evidence

class EvidenceGapOverviewTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(summarize_spoor2_evidence([],{})["rows"],[])
    def test_missing_evidence(self):
        r=summarize_spoor2_evidence([{"isin":"DE0006231004"}],{})
        self.assertEqual(len(r["rows"][0]["evidence_gaps"]),5)
        self.assertFalse(any(x["verified"] for x in r["rows"][0]["evidence_gaps"]))
    def test_self_assertion_cannot_verify(self):
        r=summarize_spoor2_evidence([{"isin":"DE0006231004"}],
                                    {"DE0006231004":{"source_attested":True}})
        self.assertTrue(r["rows"][0]["evidence_gaps"][0]["reported"])
        self.assertFalse(r["rows"][0]["evidence_gaps"][0]["verified"])
    def test_duplicate_fails(self):
        r=summarize_spoor2_evidence([{"isin":"X"},{"isin":"X"}],{})
        self.assertEqual(r["blocks"],["DUPLICATE_INSTRUMENT"])
    def test_invalid_instrument(self):
        self.assertEqual(summarize_spoor2_evidence([{}],{})["status"],"BLOCKED")
    def test_invalid_evidence(self):
        self.assertEqual(summarize_spoor2_evidence([],[])["blocks"],["INVALID_INPUT"])
    def test_deterministic_sort(self):
        r=summarize_spoor2_evidence([{"isin":"Z"},{"isin":"A"}],{})
        self.assertEqual([x["isin"] for x in r["rows"]],["A","Z"])
    def test_preserves_blocks(self):
        r=summarize_spoor2_evidence([{"isin":"X"}],{"X":{"blocks":["B","A","B"]}})
        self.assertEqual(r["rows"][0]["audit_blocks"],["A","B"])
    def test_invalid_blocks(self):
        r=summarize_spoor2_evidence([{"isin":"X"}],{"X":{"blocks":[1]}})
        self.assertIn("AUDIT_BLOCKS_MISSING_OR_INVALID",r["rows"][0]["audit_blocks"])
    def test_no_orders(self):
        r=summarize_spoor2_evidence([{"isin":"X"}],{"X":{"trade_ready":True}})
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])
        self.assertFalse(r["notify"])

if __name__=="__main__":
    unittest.main()
