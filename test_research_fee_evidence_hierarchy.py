"""Synthetic tests for research fee evidence hierarchy."""
import unittest
from research_fee_evidence_hierarchy import classify_fee_evidence as classify

class FeeEvidenceHierarchyTests(unittest.TestCase):
    def test_public_schedule_is_never_account_verified(self):
        r = classify({"evidence_kind": "OFFICIAL_PUBLIC_SCHEDULE"})
        self.assertEqual(r["status"], "PUBLIC_FEE_ASSUMPTION_ONLY")
        self.assertFalse(r["degiro_fee_verified"])
        self.assertFalse(r["trade_ready"])

    def test_public_schedule_cannot_claim_account_verification(self):
        r = classify({"evidence_kind": "OFFICIAL_PUBLIC_SCHEDULE",
                      "account_specific": True})
        self.assertEqual(r["reason"], "PUBLIC_SCHEDULE_CANNOT_ATTEST_ACCOUNT")

    def test_preview_claim_is_not_authenticated(self):
        r = classify({"evidence_kind": "BROKER_ORDER_PREVIEW",
                      "isin": "DE0006231004", "operating_mic": "XETR",
                      "preview_isin": "DE0006231004",
                      "preview_operating_mic": "XETR",
                      "preview_quantity": 50})
        self.assertEqual(r["status"], "UNAUTHENTICATED_ORDER_PREVIEW_CLAIM")
        self.assertFalse(r["degiro_fee_verified"])

    def test_preview_wrong_venue_blocks(self):
        r = classify({"evidence_kind": "BROKER_ORDER_PREVIEW",
                      "isin": "DE0006231004", "operating_mic": "XETR",
                      "preview_isin": "DE0006231004",
                      "preview_operating_mic": "XAMS",
                      "preview_quantity": 50})
        self.assertEqual(r["status"], "FEE_EVIDENCE_BLOCKED")

    def test_preview_missing_quantity_blocks(self):
        r = classify({"evidence_kind": "BROKER_ORDER_PREVIEW",
                      "isin": "DE0006231004", "operating_mic": "XETR",
                      "preview_isin": "DE0006231004",
                      "preview_operating_mic": "XETR"})
        self.assertEqual(r["reason"], "PREVIEW_IDENTITY_OR_QUANTITY_MISMATCH")

if __name__ == "__main__":
    unittest.main()
