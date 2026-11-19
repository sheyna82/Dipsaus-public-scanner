import unittest
from research.spoor2_instrument_evidence_ledger_20261113 import build_instrument_evidence_ledger

ISO = {"iso_operating_mic_found": True, "iso_regulated_segment_candidate": "XETA"}
ROWS = [{"isin": isin, "market_mic": "XETR", "market_segment": "045", "reporting_market": "XETA"}
        for isin in ("DE0006231004", "DE0007030009")]
AUDIT = {"records": ROWS, "reporting_market_reference_matched": True}

class InstrumentEvidenceLedgerTests(unittest.TestCase):
    def test_matching_official_reporting_mic_is_not_trade_authority(self):
        out = build_instrument_evidence_ledger(AUDIT, ISO)
        self.assertEqual(len(out["instruments"]), 2)
        self.assertEqual([r["reporting_mic_evidence"]["stage"] for r in out["instruments"]],
                         ["OFFICIAL_REFERENCE_MATCHED"] * 2)
        self.assertTrue(all(r["execution_mic_evidence"]["stage"] == "UNVERIFIED" for r in out["instruments"]))
        for key in ("trade_ready", "order_placement_enabled", "broker_route_verified",
                    "degiro_fee_verified", "segment_mic_verified"):
            self.assertFalse(out[key])

    def test_unverified_iso_relationship_downgrades_reporting(self):
        out = build_instrument_evidence_ledger(AUDIT, {})
        self.assertTrue(all(r["reporting_mic_evidence"]["stage"] == "UNVERIFIED" for r in out["instruments"]))

    def test_reporting_mismatch_downgrades_only_affected_instrument(self):
        rows = [dict(r) for r in ROWS]
        rows[1]["reporting_market"] = "XETU"
        out = build_instrument_evidence_ledger({"records": rows, "reporting_market_reference_matched": True}, ISO)
        self.assertEqual(out["instruments"][1]["reporting_mic_evidence"]["stage"], "UNVERIFIED")
        self.assertFalse(out["trade_ready"])

    def test_duplicate_isin_blocks(self):
        out = build_instrument_evidence_ledger({"records": [ROWS[0], ROWS[0]], "reporting_market_reference_matched": True}, ISO)
        self.assertIn("DUPLICATE_OR_UNEXPECTED_ISIN", out["blocks"])

    def test_invalid_date_blocks(self):
        out = build_instrument_evidence_ledger(AUDIT, ISO, "13-11-2026")
        self.assertIn("INVALID_AS_OF_DATE", out["blocks"])

    def test_untrusted_broker_claim_cannot_authorize(self):
        untrusted = dict(AUDIT, broker_route_verified=True, degiro_fee_verified=True, trade_ready=True)
        out = build_instrument_evidence_ledger(untrusted, dict(ISO, trade_ready=True))
        self.assertFalse(out["trade_ready"])
        self.assertFalse(out["order_placement_enabled"])

if __name__ == "__main__":
    unittest.main()
