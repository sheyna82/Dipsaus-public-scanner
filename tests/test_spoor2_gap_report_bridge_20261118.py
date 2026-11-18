import unittest
from research.spoor2_gap_report_bridge_20261118 import build_spoor2_gap_report

class GapBridgeTests(unittest.TestCase):
    def test_missing_all(self):
        r=build_spoor2_gap_report([{"isin":"DE0006231004"}],{})
        self.assertIn("AUDIT_BUNDLE_MISSING",r["rows"][0]["audit_blocks"])
        self.assertEqual(len(r["rows"][0]["audit_sources"]),6)
        self.assertFalse(r["trade_ready"])
    def test_all_reported_positive_still_blocked(self):
        audits={k:{"status":"VERIFIED","blocks":[]} for k in ("instrument","mic","xetra","degiro","fees","manifest")}
        r=build_spoor2_gap_report([{"isin":"DE0007030009"}],{"DE0007030009":audits})
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])
        self.assertTrue(all(not x["verified"] for x in r["rows"][0]["evidence_gaps"]))
    def test_aggregates_blocks(self):
        r=build_spoor2_gap_report([{"isin":"X"}],{"X":{"mic":{"status":"BLOCKED","blocks":["NO_MIC"]}}})
        self.assertIn("MIC:NO_MIC",r["rows"][0]["audit_blocks"])
        self.assertIn("XETRA_AUDIT_MISSING",r["rows"][0]["audit_blocks"])
    def test_invalid(self):
        self.assertEqual(build_spoor2_gap_report([],[])["blocks"],["INVALID_INPUT"])
    def test_duplicate(self):
        r=build_spoor2_gap_report([{"isin":"X"},{"isin":"X"}],{})
        self.assertEqual(r["blocks"],["DUPLICATE_INSTRUMENT"])
    def test_no_notify(self):
        r=build_spoor2_gap_report([{"isin":"X"}],{})
        self.assertFalse(r["notify"])
        self.assertFalse(r["automatic_orders"])

if __name__=="__main__":
    unittest.main()
