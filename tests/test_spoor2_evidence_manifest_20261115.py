"""Synthetic regression tests for the offline, non-attesting evidence manifest."""
import hashlib
import unittest

from research.spoor2_evidence_manifest_20261115 import build_evidence_manifest


def record(source, data):
    return {
        "source_id": source, "artifact_bytes": data,
        "artifact_sha256": hashlib.sha256(data).hexdigest(),
        "artifact_size": len(data),
    }


class EvidenceManifestTests(unittest.TestCase):
    def test_distinct_bytes_still_never_attest_authority(self):
        r = build_evidence_manifest((record("Alpha", b"one"), record("Beta", b"two")))
        self.assertTrue(r["manifest_complete"])
        self.assertTrue(r["byte_integrity_checked"])
        self.assertEqual(r["duplicate_source_ids"], [])
        self.assertEqual(r["shared_artifact_hashes"], [])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["blocks"], ["CALLER_SUPPLIED_MANIFEST_NOT_INDEPENDENT_ATTESTATION"])
        for flag in ("independent_source_authority_verified", "source_attested",
                     "instrument_segment_verified", "broker_route_verified",
                     "trade_ready", "order_placement_enabled"):
            self.assertFalse(r[flag])

    def test_order_independent_manifest_digest(self):
        a, b = record("Alpha", b"one"), record("Beta", b"two")
        first = build_evidence_manifest((a, b))
        second = build_evidence_manifest((b, a))
        self.assertEqual(first["records"], second["records"])
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])

    def test_case_alias_detected(self):
        r = build_evidence_manifest((record("Publisher", b"one"),
                                     record("publisher", b"two")))
        self.assertEqual(r["duplicate_source_ids"], ["publisher"])
        self.assertIn("DUPLICATE_SOURCE_IDENTIFIERS", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_identical_bytes_under_distinct_labels_detected(self):
        a, b = record("Alpha", b"same"), record("Beta", b"same")
        r = build_evidence_manifest((a, b))
        self.assertEqual(r["shared_artifact_hashes"], [a["artifact_sha256"]])
        self.assertIn("SHARED_ARTIFACT_ACROSS_SOURCE_LABELS", r["blocks"])
        self.assertFalse(r["source_attested"])

    def test_tampering_blocks_before_manifest(self):
        a = record("Alpha", b"one")
        a["artifact_bytes"] = b"tampered"
        r = build_evidence_manifest((a,))
        self.assertFalse(r["manifest_complete"])
        self.assertIsNone(r["manifest_sha256"])
        self.assertFalse(r["byte_integrity_checked"])

    def test_malformed_source_rejected(self):
        for source in ("", " Alpha", "Alpha" + chr(10) + "Beta",
                       "Alpha" + chr(0) + "Beta", "x" * 129):
            with self.subTest(source=repr(source)):
                r = build_evidence_manifest((record(source, b"one"),))
                self.assertEqual(r["blocks"], ["INVALID_SOURCE_ID"])
                self.assertFalse(r["manifest_complete"])

    def test_bad_digest_declaration_never_completes_manifest(self):
        for digest in ("", "0" * 63, "z" * 64, "0" * 65, None):
            with self.subTest(digest=digest):
                item = record("alpha", b"payload")
                item["artifact_sha256"] = digest
                r = build_evidence_manifest((item,))
                self.assertFalse(r["manifest_complete"])
                self.assertIsNone(r["manifest_sha256"])
                self.assertFalse(r["trade_ready"])

    def test_wrong_byte_size_never_completes_manifest(self):
        item = record("alpha", b"payload")
        item["artifact_size"] += 1
        r = build_evidence_manifest((item,))
        self.assertFalse(r["manifest_complete"])
        self.assertIsNone(r["manifest_sha256"])
        self.assertFalse(r["byte_integrity_checked"])

    def test_identical_repeated_record_is_not_independent_source(self):
        item = record("alpha", b"payload")
        r = build_evidence_manifest((item, item))
        self.assertTrue(r["manifest_complete"])
        self.assertEqual(r["duplicate_source_ids"], ["alpha"])
        self.assertIn("DUPLICATE_SOURCE_IDENTIFIERS", r["blocks"])
        self.assertFalse(r["independent_source_authority_verified"])

    def test_source_alias_normalization_keeps_fingerprint_stable(self):
        lower = build_evidence_manifest((record("alpha", b"one"),))
        upper = build_evidence_manifest((record("ALPHA", b"one"),))
        self.assertEqual(lower["manifest_sha256"], upper["manifest_sha256"])
        self.assertFalse(lower["source_attested"])
        self.assertFalse(upper["source_attested"])

    def test_empty_and_invalid_records_block(self):
        self.assertEqual(build_evidence_manifest()["blocks"], ["EVIDENCE_RECORDS_REQUIRED"])
        self.assertEqual(build_evidence_manifest((None,))["blocks"], ["INVALID_EVIDENCE_RECORD"])


if __name__ == "__main__":
    unittest.main()
