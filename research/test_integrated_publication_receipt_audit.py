"""Regression tests for claimed historical publication receipts."""
import hashlib
import unittest
from integrated_publication_receipt_audit import audit_publication_receipts

RAW = b"archive capture fixture"
DIGEST = hashlib.sha256(RAW).hexdigest()

def registration():
    return {"id": "A", "registered_at": "2026-11-05T10:00:00+01:00",
            "source_available_at": "2026-11-05T08:30:00Z",
            "entry_at": "2026-11-06T09:00:00+01:00",
            "source_sha256": hashlib.sha256(b"synthetic source").hexdigest()}

def receipt():
    return {"id": "A", "raw_bytes": RAW, "receipt_sha256": DIGEST,
            "source_sha256": hashlib.sha256(b"synthetic source").hexdigest(),
            "observed_at": "2026-11-05T08:30:00Z",
            "source_url": "https://example.org/archive"}

class PublicationReceiptAuditTests(unittest.TestCase):
    def test_valid_receipt_remains_unproven(self):
        result = audit_publication_receipts([registration()], [receipt()])
        self.assertEqual(result["receipt_count"], 1)
        self.assertEqual(len(result["audit_sha256"]), 64)
        self.assertEqual(result["audit_fingerprint_schema"], "publication_receipt_audit_v2")
        self.assertFalse(result["external_publication_time_independently_proven"])
        self.assertFalse(result["eligible_for_performance_claim"])
        self.assertEqual(result["evidence_level"], "SUPPLIED_RECEIPT_BYTES_ONLY")
        self.assertEqual(len(result["independent_verification_requirements"]), 4)

    def test_receipt_audit_fingerprint_changes_with_evidence(self):
        baseline = audit_publication_receipts([registration()], [receipt()])
        modified = receipt()
        modified["source_url"] = "https://example.org/other-archive"
        changed = audit_publication_receipts([registration()], [modified])
        self.assertNotEqual(baseline["audit_sha256"], changed["audit_sha256"])
        self.assertEqual(baseline["audit_sha256"],
                         audit_publication_receipts([registration()], [receipt()])["audit_sha256"])

    def test_fingerprint_binds_registration_and_entry_times(self):
        baseline = audit_publication_receipts([registration()], [receipt()])
        for field, value in (("registered_at", "2026-11-05T10:01:00+01:00"),
                             ("entry_at", "2026-11-06T09:01:00+01:00"),
                             ("source_available_at", "2026-11-05T08:29:00Z")):
            with self.subTest(field=field):
                changed = registration()
                changed[field] = value
                result = audit_publication_receipts([changed], [receipt()])
                self.assertNotEqual(baseline["audit_sha256"], result["audit_sha256"])

    def test_receipt_source_binding_mismatch_rejected(self):
        r = receipt()
        r["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "RECEIPT_SOURCE_BINDING_MISMATCH"):
            audit_publication_receipts([registration()], [r])

    def test_receipt_before_claimed_source_availability_rejected(self):
        r = receipt()
        r["observed_at"] = "2026-11-05T08:29:59Z"
        reg = registration()
        reg["source_available_at"] = "2026-11-05T08:30:00Z"
        with self.assertRaisesRegex(ValueError, "RECEIPT_BEFORE_CLAIMED_SOURCE_AVAILABILITY"):
            audit_publication_receipts([reg], [r])

    def test_malformed_https_urls_rejected(self):
        for url in ("https://", "https:///archive", "https://user:pass@example.org/archive",
                    "https://example.org/path with spaces", "http://example.org/archive"):
            with self.subTest(url=url):
                r = receipt()
                r["source_url"] = url
                with self.assertRaisesRegex(ValueError, "INVALID_RECEIPT_URL"):
                    audit_publication_receipts([registration()], [r])

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
