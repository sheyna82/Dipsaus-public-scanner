"""No real providers or private identifiers: synthetic metadata only."""
import unittest
from research.us_anchor_evidence_audit_20261118 import assess_anchor_evidence

HASH = "a"*64
def receipt():
    return {"pinned_sha256": HASH, "submitted_utc": "2026-11-17T21:00:00Z",
            "receipt_utc": "2026-11-17T21:00:01Z", "provider_id": "synthetic-provider",
            "receipt_id": "synthetic-receipt", "independent_verification": True}

class AnchorEvidenceAuditTests(unittest.TestCase):
    def test_consistent_metadata_not_authentication(self):
        x = assess_anchor_evidence(HASH, receipt())
        self.assertEqual(x["status"], "RECEIPT_METADATA_CONSISTENT_ONLY")
        self.assertIn("RECEIPT_SIGNATURE_NOT_VERIFIED", x["blocks"])
        self.assertFalse(x["trade_ready"])
        self.assertFalse(x["notify"])

    def test_missing_receipt(self):
        self.assertEqual(assess_anchor_evidence(HASH, None)["status"], "BLOCKED")

    def test_wrong_hash(self):
        r = receipt(); r["pinned_sha256"] = "b"*64
        self.assertIn("PIN_MISMATCH", assess_anchor_evidence(HASH, r)["blocks"])

    def test_bad_head(self):
        self.assertEqual(assess_anchor_evidence("bad", receipt())["status"], "BLOCKED")

    def test_receipt_before_submission(self):
        r = receipt(); r["receipt_utc"] = "2026-11-17T20:59:59Z"
        self.assertEqual(assess_anchor_evidence(HASH, r)["status"], "BLOCKED")

    def test_naive_time(self):
        r = receipt(); r["submitted_utc"] = "2026-11-17T21:00:00"
        self.assertEqual(assess_anchor_evidence(HASH, r)["status"], "BLOCKED")

    def test_missing_provider(self):
        r = receipt(); r["provider_id"] = ""
        self.assertEqual(assess_anchor_evidence(HASH, r)["status"], "BLOCKED")

    def test_missing_receipt_id(self):
        r = receipt(); r["receipt_id"] = ""
        self.assertEqual(assess_anchor_evidence(HASH, r)["status"], "BLOCKED")

    def test_no_independent_verification(self):
        r = receipt(); r["independent_verification"] = False
        self.assertEqual(assess_anchor_evidence(HASH, r)["status"], "BLOCKED")

    def test_self_reported_verification_never_trade_ready(self):
        r = receipt()
        x = assess_anchor_evidence(HASH, r)
        self.assertFalse(x["order_placement_enabled"])
        self.assertIn("PROVIDER_INDEPENDENCE_NOT_VERIFIED", x["blocks"])

if __name__ == "__main__":
    unittest.main()
