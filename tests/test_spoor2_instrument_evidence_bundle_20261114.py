"""Synthetic tests for byte-checked evidence bundle orchestration."""
import hashlib
import unittest
from research.spoor2_instrument_evidence_bundle_20261114 import inspect_instrument_evidence_bundle

ISIN = "US0378331005"
MIC = "XNAS"


def record(source, mic=MIC, data=None):
    data = data if data is not None else ("synthetic:" + source).encode()
    return {
        "source_id": source, "isin": ISIN, "mic": mic,
        "artifact_bytes": data, "artifact_sha256": hashlib.sha256(data).hexdigest(),
        "artifact_size": len(data),
    }


class EvidenceBundleTests(unittest.TestCase):
    def test_empty_bundle_blocks(self):
        self.assertEqual(inspect_instrument_evidence_bundle(ISIN, MIC)["blocks"],
                         ["EVIDENCE_RECORDS_REQUIRED"])

    def test_two_byte_checked_sources_still_block_trade(self):
        r = inspect_instrument_evidence_bundle(ISIN, MIC, (record("a"), record("b")))
        self.assertTrue(r["byte_integrity_checked"])
        self.assertTrue(r["reported_cross_source_agreement"])
        self.assertFalse(r["independent_source_authority_verified"])
        self.assertEqual(r["status"], "BLOCKED")
        for flag in ("source_attested", "instrument_segment_verified",
                     "broker_route_verified", "trade_ready", "order_placement_enabled"):
            self.assertFalse(r[flag])

    def test_reconciled_bundle_includes_deterministic_manifest(self):
        a, b = record("a"), record("b")
        forward = inspect_instrument_evidence_bundle(ISIN, MIC, (a, b))
        reverse = inspect_instrument_evidence_bundle(ISIN, MIC, (b, a))
        self.assertTrue(forward["manifest_complete"])
        self.assertEqual(len(forward["manifest_sha256"]), 64)
        self.assertEqual(forward["manifest_sha256"], reverse["manifest_sha256"])
        self.assertTrue(forward["reported_cross_source_agreement"])
        self.assertFalse(forward["trade_ready"])

    def test_conflicting_bundle_does_not_claim_manifest_complete(self):
        r = inspect_instrument_evidence_bundle(
            ISIN, MIC, (record("a"), record("b", mic="XETR")))
        self.assertFalse(r["manifest_complete"])
        self.assertIsNone(r["manifest_sha256"])
        self.assertFalse(r["reported_cross_source_agreement"])

    def test_tampered_artifact_blocks_before_reconciliation(self):
        b = record("b")
        b["artifact_bytes"] += b"tampered"
        r = inspect_instrument_evidence_bundle(ISIN, MIC, (record("a"), b))
        self.assertEqual(r["blocks"], ["ARTIFACT_BYTE_COUNT_MISMATCH"])
        self.assertFalse(r["byte_integrity_checked"])

    def test_two_labels_one_artifact_blocks(self):
        data = b"same"
        r = inspect_instrument_evidence_bundle(ISIN, MIC,
                                               (record("a", data=data), record("b", data=data)))
        self.assertEqual(r["blocks"], ["DISTINCT_ARTIFACT_HASHES_REQUIRED"])

    def test_conflicting_mic_blocks(self):
        r = inspect_instrument_evidence_bundle(ISIN, MIC, (record("a"), record("b", mic="XETR")))
        self.assertEqual(r["blocks"], ["CROSS_SOURCE_INSTRUMENT_CONFLICT"])
        self.assertFalse(r["independent_source_authority_verified"])

    def test_source_alias_blocks(self):
        r = inspect_instrument_evidence_bundle(ISIN, MIC, (record("Publisher"), record("publisher")))
        self.assertEqual(r["blocks"], ["INTRA_SOURCE_ARTIFACT_CONFLICT"])

    def test_non_dict_record_blocks(self):
        r = inspect_instrument_evidence_bundle(ISIN, MIC, (record("a"), None))
        self.assertEqual(r["blocks"], ["INVALID_EVIDENCE_RECORD"])

    def test_missing_bytes_blocks(self):
        a = record("a")
        del a["artifact_bytes"]
        r = inspect_instrument_evidence_bundle(ISIN, MIC, (a, record("b")))
        self.assertEqual(r["blocks"], ["NONEMPTY_ARTIFACT_BYTES_REQUIRED"])


if __name__ == "__main__":
    unittest.main()
