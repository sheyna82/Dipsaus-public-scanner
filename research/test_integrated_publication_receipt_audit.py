"""Regression tests for claimed historical publication receipts."""
import hashlib
import unittest
from integrated_publication_receipt_audit import audit_publication_receipts

RAW = b"archive capture fixture"
DIGEST = hashlib.sha256(RAW).hexdigest()

def registration():
    return {"id": "A", "registered_at": "2026-11-05T10:00:00+01:00",
            "entry_at": "2026-11-06T09:00:00+01:00"}

def receipt():
    return {"id": "A", "raw_bytes": RAW, "receipt_sha256": DIGEST,
            "observed_at": "2026-11-05T08:30:00Z",
            "source_url": "https://example.org/archive"}

class PublicationReceiptAuditTests(unittest.TestCase):
    def test_valid_receipt_remains_unproven(self):
        result = audit_publication_receipts([registration()], [receipt()])
        self.assertEqual(result["receipt_count"], 1)
        self.assertFalse(result["external_publication_time_independently_proven"])
        self.assertFalse(result["eligible_for_performance_claim"])

    def test_tampered_receipt_rejected(self):
        r = receipt()
        r["raw_bytes"] += b"tampered"
        with self.assertRaisesRegex(ValueError, "RECEIPT_HASH_MISMATCH"):
            audit_publication_receipts([registration()], [r])

    def test_late_receipt_rejected(self):
        r = receipt()
        r["observed_at"] = "2026-11-05T12:00:00Z"
        with self.assertRaisesRegex(ValueError, "RECEIPT_TOO_LATE"):
            audit_publication_receipts([registration()], [r])

    def test_missing_receipt_rejected(self):
        with self.assertRaisesRegex(ValueError, "RECEIPT_COVERAGE_MISMATCH"):
            audit_publication_receipts([registration()], [])

    def test_duplicate_receipt_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_RECEIPT"):
            audit_publication_receipts([registration()], [receipt(), receipt()])

    def test_naive_timestamp_rejected(self):
        r = receipt()
        r["observed_at"] = "2026-11-05T08:30:00"
        with self.assertRaisesRegex(ValueError, "NAIVE_TIMESTAMP"):
            audit_publication_receipts([registration()], [r])

if __name__ == "__main__":
    unittest.main()
