import unittest
from research.spoor2_degiro_public_evidence_20261113 import assess_public_degiro_evidence, SOURCES

ROWS = [{"isin": "DE0006231004"}, {"isin": "DE0007030009"}]

class PublicDegiroEvidenceTests(unittest.TestCase):
    def test_official_links_cannot_authorize_trade(self):
        out = assess_public_degiro_evidence({"instruments": ROWS})
        self.assertEqual(out["status"], "BLOCKED")
        self.assertEqual(len(out["instruments"]), 2)
        for field in ("account_execution_route_verified", "account_tariff_verified",
                      "broker_route_verified", "degiro_fee_verified",
                      "trade_ready", "order_placement_enabled"):
            self.assertFalse(out[field])
        self.assertTrue(all(r["degiro_execution_route"] is None for r in out["instruments"]))

    def test_missing_ledger_blocks(self):
        self.assertIn("INVALID_INSTRUMENT_LEDGER", assess_public_degiro_evidence(None)["blocks"])

    def test_duplicate_isin_blocks(self):
        out = assess_public_degiro_evidence({"instruments": [ROWS[0], ROWS[0]]})
        self.assertIn("INCOMPLETE_OR_INVALID_INSTRUMENT_SET", out["blocks"])

    def test_untrusted_account_claims_ignored(self):
        out = assess_public_degiro_evidence({"instruments": [dict(r, trade_ready=True, degiro_fee_verified=True) for r in ROWS], "trade_ready": True})
        self.assertFalse(out["trade_ready"])
        self.assertTrue(all(r["account_specific_fee"] is None for r in out["instruments"]))

    def test_sources_are_official_https(self):
        self.assertTrue(SOURCES)
        self.assertTrue(all(u.startswith("https://www.degiro.nl/") for u in SOURCES.values()))

    def test_fx_and_connectivity_not_assumed(self):
        out = assess_public_degiro_evidence({"instruments": ROWS})
        self.assertTrue(all(r["fx_fee_applicability"] == "UNDETERMINED" and
                            r["connectivity_fee_applicability"] == "UNDETERMINED"
                            for r in out["instruments"]))

if __name__ == "__main__":
    unittest.main()
