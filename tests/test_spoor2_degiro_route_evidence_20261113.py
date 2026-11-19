import unittest
from research.spoor2_degiro_route_evidence_20261113 import classify_degiro_route_evidence as classify

ISIN = "DE0006231004"

class DegiroRouteEvidenceTests(unittest.TestCase):
    def test_public_venue_not_execution(self):
        out = classify(ISIN, public_venue={"venue": "XETRA"})
        self.assertEqual(out["evidence_stage"], "PUBLIC_VENUE_LISTED")
        self.assertIsNone(out["executed_venue"])
        self.assertFalse(out["broker_route_verified"])

    def test_order_entry_selection_not_execution(self):
        out = classify(ISIN, order_entry={"isin": ISIN, "venue": "XETR"})
        self.assertEqual(out["evidence_stage"], "ORDER_ENTRY_SELECTION")
        self.assertIsNone(out["executed_venue"])

    def test_unattested_execution_claim_never_verifies(self):
        out = classify(ISIN, execution={"isin": ISIN, "venue": "XETRA", "verified": True})
        self.assertEqual(out["evidence_stage"], "EXECUTION_CONFIRMATION_UNATTESTED")
        for key in ("execution_venue_verified", "broker_route_verified",
                    "degiro_fee_verified", "trade_ready", "order_placement_enabled"):
            self.assertFalse(out[key])

    def test_wrong_isin_cannot_leak_between_instruments(self):
        out = classify(ISIN, execution={"isin": "DE0007030009", "venue": "XETRA"})
        self.assertIsNone(out["executed_venue"])

    def test_unknown_isin_blocks(self):
        out = classify("UNKNOWN", public_venue={"venue": "XETRA"})
        self.assertIn("UNKNOWN_PILOT_ISIN", out["blocks"])

    def test_unrecognized_venue_blocks_promotion(self):
        out = classify(ISIN, order_entry={"isin": ISIN, "venue": "UNKNOWN"})
        self.assertEqual(out["evidence_stage"], "UNVERIFIED")
        self.assertFalse(out["trade_ready"])

if __name__ == "__main__":
    unittest.main()
