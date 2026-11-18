import unittest
from research.spoor2_pilot_gap_report_20261118 import build_pilot_gap_report

class PilotGapReportTests(unittest.TestCase):
    def test_pilot_identifiers(self):
        r=build_pilot_gap_report()
        self.assertEqual([x["isin"] for x in r["rows"]],["DE0006231004","DE0007030009","FI0009000681","NL0010273215"])
    def test_four_pilot_markets_are_unverified_claims(self):
        from research.spoor2_pilot_gap_report_20261118 import PILOT
        r=build_pilot_gap_report()
        self.assertEqual(
            [(x["symbol"],x["operating_mic"]) for x in PILOT],
            [("ASML.AS","XAMS"),("IFX.DE","XETR"),
             ("NOKIA.HE","XHEL"),("RHM.DE","XETR")]
        )
        self.assertEqual(r["integration_status"],"RESEARCH_ONLY_UNATTESTED")

    def test_every_audit_is_blocked(self):
        r=build_pilot_gap_report()
        for row in r["rows"]:
            self.assertEqual(len(row["audit_sources"]),6)
            self.assertTrue(all(v=="REPORTED_BLOCKED" for v in row["audit_sources"].values()))
    def test_no_verified_evidence(self):
        r=build_pilot_gap_report()
        self.assertTrue(all(not gate["verified"] for row in r["rows"] for gate in row["evidence_gaps"]))
    def test_no_execution(self):
        r=build_pilot_gap_report()
        for key in ("trade_ready","order_placement_enabled","notify","automatic_orders"):
            self.assertFalse(r[key])
    def test_no_fresh_capture_claim(self):
        r=build_pilot_gap_report()
        self.assertFalse(r["fresh_external_capture"])
        self.assertIn("2026-11-23",r["iso_effective_date_warning"])
    def test_missing_broker_route_explicit(self):
        r=build_pilot_gap_report()
        for row in r["rows"]:
            self.assertIn("DEGIRO:ACCOUNT_EXECUTION_ROUTE_NOT_ATTESTED",row["audit_blocks"])

if __name__=="__main__":
    unittest.main()
