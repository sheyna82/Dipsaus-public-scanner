"""Offline regression tests for reporting MIC, not execution MIC."""
import unittest
from research.spoor2_xetra_reporting_market_audit_20261113 import audit_reporting_market

ISO = {"iso_operating_mic_found": True, "iso_regulated_segment_candidate": "XETA"}

def fixture(first="XETA", second="XETA", duplicate=False):
    lines = ["Market:;XETR", "Date Last Update:;13.11.2026",
             "ISIN;MIC Code;Market Segment;Reporting Market",
             "DE0006231004;XETR;045;" + first,
             "DE0007030009;XETR;045;" + second]
    if duplicate:
        lines.append(lines[-1])
    return ("\n".join(lines) + "\n").encode()

class ReportingMarketAuditTests(unittest.TestCase):
    def test_matching_reporting_mics_do_not_authorize_trades(self):
        out = audit_reporting_market(fixture(), ISO)
        self.assertTrue(out["reporting_market_reference_matched"])
        self.assertEqual([r["reporting_market"] for r in out["records"]], ["XETA", "XETA"])
        for field in ("instrument_segment_verified", "segment_mic_verified",
                      "broker_route_verified", "degiro_fee_verified",
                      "source_attested", "trade_ready", "order_placement_enabled"):
            self.assertFalse(out[field], field)

    def test_mismatched_reporting_market_blocks(self):
        out = audit_reporting_market(fixture(second="XETB"), ISO)
        self.assertFalse(out["reporting_market_reference_matched"])
        self.assertIn("INSTRUMENT_REPORTING_MARKET_MISMATCH", out["blocks"])

    def test_duplicate_instrument_blocks(self):
        out = audit_reporting_market(fixture(duplicate=True), ISO)
        self.assertFalse(out["reporting_market_reference_matched"])
        self.assertIn("XETRA_REPORTING_MARKET_PARSE_FAILED", out["blocks"])

    def test_unconfirmed_iso_relationship_blocks(self):
        out = audit_reporting_market(fixture(), {"iso_operating_mic_found": True})
        self.assertFalse(out["reporting_market_reference_matched"])
        self.assertIn("ISO_RELATIONSHIP_NOT_CONFIRMED", out["blocks"])

    def test_invalid_row_width_blocks(self):
        out = audit_reporting_market(fixture() + b"EXTRA;XETR\n", ISO)
        self.assertIn("XETRA_REPORTING_MARKET_PARSE_FAILED", out["blocks"])

if __name__ == "__main__":
    unittest.main()
