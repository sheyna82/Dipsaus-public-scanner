"""End-to-end source-hash-backed selection regression tests."""
import hashlib
import json
import unittest
from integrated_hash_checked_priority_selection import compare_hash_checked, verify_manifest_fingerprint

RAW_A, RAW_B = b"synthetic source A", b"synthetic source B"
HASH_A, HASH_B = hashlib.sha256(RAW_A).hexdigest(), hashlib.sha256(RAW_B).hexdigest()

def registration(i, priority, digest):
    return {"id": i, "registered_at": "2026-11-05T10:00:00+01:00",
            "source_available_at": "2026-11-05T08:30:00Z",
            "entry_at": "2026-11-06T09:00:00+01:00",
            "source_verified": True, "immutable_registration_verified": True,
            "source_sha256": digest, "registered_priority": priority}

def candidate(i):
    return {"id": i, "entry_date": "2026-11-06", "exit_date": "2026-11-12",
            "allocation_eur": 30000, "research_only": True, "trade_ready": False}

class HashCheckedSelectionTests(unittest.TestCase):
    def test_valid_source_bytes_selects_registered_priority(self):
        result = compare_hash_checked([registration("A", 1, HASH_A), registration("B", 3, HASH_B)],
                                      {HASH_A: RAW_A, HASH_B: RAW_B},
                                      [candidate("A"), candidate("B")])
        self.assertEqual(result["hash_checked_count"], 2)
        manifest = result["research_manifest"]
        self.assertEqual(manifest["source_sha256"], sorted([HASH_A, HASH_B]))
        self.assertEqual(manifest["schema"], "hash_checked_selection_manifest_v2")
        self.assertEqual(len(manifest["manifest_sha256"]), 64)
        self.assertEqual(manifest["input_sha256"], result["selection"]["input_sha256"])
        self.assertEqual(manifest["cash_policy"], "exit_before_entry_same_day")
        self.assertFalse(manifest["historical_authenticity_independently_proven"])
        self.assertFalse(manifest["external_publication_time_independently_proven"])
        self.assertFalse(manifest["eligible_for_performance_claim"])
        self.assertEqual(manifest["source_provenance_status"], "CLAIMED_TIMESTAMPS_NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual([r["id"] for r in manifest["registration_evidence"]], ["A", "B"])
        self.assertEqual(manifest["registration_evidence"][0]["source_sha256"], HASH_A)
        self.assertEqual(manifest["registration_evidence"][0]["source_available_at_claimed"], "2026-11-05T08:30:00Z")
        self.assertFalse(manifest["trade_ready"])
        self.assertEqual(result["selection"]["priority"]["accepted_ids"], ["B"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["historical_authenticity_independently_proven"])

    def test_cash_policy_propagates_through_hash_checked_gate(self):
        first = candidate("A")
        first["allocation_eur"] = 50000
        first["exit_date"] = "2026-11-09"
        second = candidate("B")
        second["allocation_eur"] = 50000
        second["entry_date"] = "2026-11-09"
        second["exit_date"] = "2026-11-13"
        regs = [registration("A", 1, HASH_A), registration("B", 3, HASH_B)]
        regs[1]["entry_at"] = "2026-11-09T09:00:00+01:00"
        # B's registration and its candidate date must match; both source hashes are verified.
        source = {HASH_A: RAW_A, HASH_B: RAW_B}
        immediate = compare_hash_checked(regs, source, [first, second], same_day_cash_reuse=True)
        conservative = compare_hash_checked(regs, source, [first, second], same_day_cash_reuse=False)
        self.assertEqual(immediate["selection"]["baseline"]["accepted_ids"], ["A", "B"])
        self.assertEqual(conservative["selection"]["baseline"]["accepted_ids"], ["A"])
        self.assertEqual(conservative["selection"]["priority"]["accepted_ids"], ["A"])
        self.assertFalse(conservative["selection"]["same_day_cash_reuse"])
        self.assertEqual(conservative["research_manifest"]["cash_policy"], "entry_before_exit_same_day")
        self.assertNotEqual(immediate["research_manifest"]["input_sha256"], conservative["research_manifest"]["input_sha256"])

    def test_receipt_audit_attached_without_authenticity_promotion(self):
        raw_receipt = b"synthetic capture receipt"
        receipt = {"id": "A", "raw_bytes": raw_receipt,
                   "receipt_sha256": hashlib.sha256(raw_receipt).hexdigest(),
                   "source_sha256": HASH_A,
                   "observed_at": "2026-11-05T08:30:00Z",
                   "source_url": "https://example.org/archive"}
        result = compare_hash_checked([registration("A", 1, HASH_A)],
                                      {HASH_A: RAW_A}, [candidate("A")],
                                      publication_receipts=[receipt])
        manifest = result["research_manifest"]
        self.assertTrue(manifest["publication_receipts_supplied"])
        self.assertEqual(manifest["publication_receipt_audit"]["receipt_count"], 1)
        self.assertFalse(manifest["eligible_for_performance_claim"])

    def test_manifest_hash_changes_with_receipt_and_is_repeatable(self):
        raw = b"synthetic capture receipt"
        receipt = {"id": "A", "raw_bytes": raw,
                   "receipt_sha256": hashlib.sha256(raw).hexdigest(),
                   "source_sha256": HASH_A,
                   "observed_at": "2026-11-05T08:30:00Z",
                   "source_url": "https://example.org/archive"}
        args = ([registration("A", 1, HASH_A)], {HASH_A: RAW_A}, [candidate("A")])
        baseline = compare_hash_checked(*args, publication_receipts=[receipt])
        repeated = compare_hash_checked(*args, publication_receipts=[receipt])
        changed_receipt = dict(receipt, source_url="https://example.org/other-archive")
        changed = compare_hash_checked(*args, publication_receipts=[changed_receipt])
        self.assertEqual(baseline["research_manifest"]["manifest_sha256"],
                         repeated["research_manifest"]["manifest_sha256"])
        self.assertNotEqual(baseline["research_manifest"]["manifest_sha256"],
                            changed["research_manifest"]["manifest_sha256"])
        self.assertNotEqual(baseline["research_manifest"]["manifest_sha256"],
                            compare_hash_checked(*args)["research_manifest"]["manifest_sha256"])

    def test_archived_manifest_verification_detects_tampering(self):
        result = compare_hash_checked([registration("A", 1, HASH_A)],
                                      {HASH_A: RAW_A}, [candidate("A")])
        manifest = result["research_manifest"]
        verified = verify_manifest_fingerprint(manifest)
        self.assertTrue(verified["fingerprint_verified"])
        self.assertFalse(verified["historical_authenticity_independently_proven"])
        modified = dict(manifest, capital_eur=100000)
        with self.assertRaisesRegex(ValueError, "MANIFEST_FINGERPRINT_MISMATCH"):
            verify_manifest_fingerprint(modified)
        with self.assertRaisesRegex(ValueError, "INVALID_MANIFEST_FINGERPRINT"):
            verify_manifest_fingerprint(dict(manifest, manifest_sha256="bad"))
        with self.assertRaisesRegex(ValueError, "INVALID_MANIFEST_SCHEMA"):
            verify_manifest_fingerprint(dict(manifest, schema="unknown"))

    def test_manifest_verifier_rejects_rehashed_evidence_promotion(self):
        manifest = compare_hash_checked([registration("A", 1, HASH_A)],
                                        {HASH_A: RAW_A}, [candidate("A")])["research_manifest"]
        forged = dict(manifest, eligible_for_performance_claim=True)
        payload = {k: v for k, v in forged.items() if k != "manifest_sha256"}
        forged["manifest_sha256"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_EVIDENCE_PROMOTION"):
            verify_manifest_fingerprint(forged)

    def test_manifest_verifier_checks_nested_receipt_audit(self):
        raw = b"synthetic capture receipt"
        receipt = {"id": "A", "raw_bytes": raw,
                   "receipt_sha256": hashlib.sha256(raw).hexdigest(),
                   "source_sha256": HASH_A, "observed_at": "2026-11-05T08:30:00Z",
                   "source_url": "https://example.org/archive"}
        manifest = compare_hash_checked([registration("A", 1, HASH_A)],
                                        {HASH_A: RAW_A}, [candidate("A")],
                                        publication_receipts=[receipt])["research_manifest"]
        self.assertTrue(verify_manifest_fingerprint(manifest)["fingerprint_verified"])
        audit = dict(manifest["publication_receipt_audit"], audit_sha256="0" * 64)
        forged = dict(manifest, publication_receipt_audit=audit)
        payload = {k: v for k, v in forged.items() if k != "manifest_sha256"}
        forged["manifest_sha256"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "RECEIPT_AUDIT_FINGERPRINT_MISMATCH"):
            verify_manifest_fingerprint(forged)

    def test_rehashed_receipt_and_manifest_cannot_change_registration_binding(self):
        raw = b"synthetic capture receipt"
        receipt = {"id": "A", "raw_bytes": raw,
                   "receipt_sha256": hashlib.sha256(raw).hexdigest(),
                   "source_sha256": HASH_A, "observed_at": "2026-11-05T08:30:00Z",
                   "source_url": "https://example.org/archive"}
        manifest = compare_hash_checked([registration("A", 1, HASH_A)],
                                        {HASH_A: RAW_A}, [candidate("A")],
                                        publication_receipts=[receipt])["research_manifest"]
        forged = dict(manifest)
        audit = dict(forged["publication_receipt_audit"])
        changed_receipt = dict(audit["receipts"][0], registered_at_claimed="2026-11-05T10:01:00+01:00")
        audit["receipts"] = [changed_receipt]
        audit["audit_sha256"] = hashlib.sha256(
            json.dumps(audit["receipts"], sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
        forged["publication_receipt_audit"] = audit
        payload = {k: v for k, v in forged.items() if k != "manifest_sha256"}
        forged["manifest_sha256"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "RECEIPT_REGISTRATION_BINDING_MISMATCH"):
            verify_manifest_fingerprint(forged)

    def test_invalid_receipt_blocks_selection(self):
        bad = {"id": "A", "raw_bytes": b"bad", "receipt_sha256": "0" * 64, "source_sha256": HASH_A,
               "observed_at": "2026-11-05T08:30:00Z",
               "source_url": "https://example.org/archive"}
        with self.assertRaisesRegex(ValueError, "RECEIPT_HASH_MISMATCH"):
            compare_hash_checked([registration("A", 1, HASH_A)],
                                 {HASH_A: RAW_A}, [candidate("A")],
                                 publication_receipts=[bad])

    def test_missing_receipt_coverage_blocks_selection(self):
        with self.assertRaisesRegex(ValueError, "RECEIPT_COVERAGE_MISMATCH"):
            compare_hash_checked([registration("A", 1, HASH_A)],
                                 {HASH_A: RAW_A}, [candidate("A")],
                                 publication_receipts=[])

    def test_receipt_bound_to_different_verified_source_blocks_selection(self):
        raw_receipt = b"synthetic capture receipt"
        receipt = {"id": "A", "raw_bytes": raw_receipt,
                   "receipt_sha256": hashlib.sha256(raw_receipt).hexdigest(),
                   "source_sha256": HASH_B,
                   "observed_at": "2026-11-05T08:30:00Z",
                   "source_url": "https://example.org/archive"}
        with self.assertRaisesRegex(ValueError, "RECEIPT_SOURCE_BINDING_MISMATCH"):
            compare_hash_checked([registration("A", 1, HASH_A)],
                                 {HASH_A: RAW_A, HASH_B: RAW_B},
                                 [candidate("A")], publication_receipts=[receipt])

    def test_tampered_source_blocks_selection(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH_MISMATCH"):
            compare_hash_checked([registration("A", 1, HASH_A)],
                                 {HASH_A: RAW_A + b"changed"}, [candidate("A")])

    def test_missing_source_blocks_selection(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_MISSING"):
            compare_hash_checked([registration("A", 1, HASH_A)], {}, [candidate("A")])

    def test_missing_candidate_registration_blocks(self):
        with self.assertRaisesRegex(ValueError, "CANDIDATE_REGISTRATION_COVERAGE_MISMATCH"):
            compare_hash_checked([registration("A", 1, HASH_A)],
                                 {HASH_A: RAW_A}, [candidate("A"), candidate("B")])

    def test_source_after_registration_blocks(self):
        r = registration("A", 1, HASH_A)
        r["source_available_at"] = "2026-11-05T12:00:00Z"
        with self.assertRaisesRegex(ValueError, "POINT_IN_TIME_VIOLATION"):
            compare_hash_checked([r], {HASH_A: RAW_A}, [candidate("A")])

if __name__ == "__main__":
    unittest.main()
