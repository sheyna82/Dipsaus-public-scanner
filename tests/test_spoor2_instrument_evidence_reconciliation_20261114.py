"""Offline reconciliation tests; evidence records are synthetic, not exchange claims."""
import unittest
from research.spoor2_instrument_evidence_reconciliation_20261114 import reconcile_instrument_evidence

ISIN = "US0378331005"
MIC = "XNAS"
HASH = "a" * 64


def record(source, mic=MIC, isin=ISIN, digest=HASH):
    return {"source_id": source, "isin": isin, "mic": mic, "artifact_sha256": ("b" * 64 if source == "b" and digest == HASH else digest)}


class InstrumentEvidenceReconciliationTests(unittest.TestCase):
    def test_missing_evidence_blocks(self):
        self.assertEqual(reconcile_instrument_evidence(ISIN, MIC)["blocks"],
                         ["EVIDENCE_RECORDS_REQUIRED"])

    def test_one_source_blocks(self):
        self.assertEqual(reconcile_instrument_evidence(ISIN, MIC, (record("a"),))["blocks"],
                         ["TWO_DISTINCT_SOURCES_REQUIRED"])

    def test_duplicate_source_is_not_independent(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("a"), record("a")))
        self.assertEqual(r["blocks"], ["TWO_DISTINCT_SOURCES_REQUIRED"])

    def test_two_agreeing_records_still_block_trade(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("a"), record("b")))
        self.assertTrue(r["independent_agreement"])
        self.assertEqual(r["source_count"], 2)
        for key in ("source_attested", "instrument_segment_verified",
                    "broker_route_verified", "trade_ready", "order_placement_enabled"):
            self.assertFalse(r[key])

    def test_cross_source_conflict_blocks(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("a"), record("b", "XETR")))
        self.assertEqual(r["blocks"], ["CROSS_SOURCE_INSTRUMENT_CONFLICT"])

    def test_intra_source_conflict_blocks(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("a"), record("a", "XETR")))
        self.assertEqual(r["blocks"], ["INTRA_SOURCE_CONFLICT"])

    def test_missing_hash_blocks(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("a", digest=""), record("b")))
        self.assertEqual(r["blocks"], ["INCOMPLETE_EVIDENCE_PROVENANCE"])

    def test_duplicate_artifact_hashes_do_not_prove_independence(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("a", digest="b" * 64), record("b")))
        self.assertEqual(r["blocks"], ["DISTINCT_ARTIFACT_HASHES_REQUIRED"])

    def test_same_source_conflicting_artifact_hash_blocks(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("a"), record("a", digest="c" * 64), record("b")))
        self.assertEqual(r["blocks"], ["INTRA_SOURCE_ARTIFACT_CONFLICT"])

    def test_case_only_source_alias_not_independent(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("Publisher"), record("publisher")))
        self.assertEqual(r["blocks"], ["INTRA_SOURCE_ARTIFACT_CONFLICT"])
        self.assertFalse(r["independent_agreement"])

    def test_case_only_alias_same_hash_not_independent(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("Publisher"), record("publisher", digest=HASH)))
        self.assertEqual(r["blocks"], ["TWO_DISTINCT_SOURCES_REQUIRED"])

    def test_bad_isin_blocks(self):
        r = reconcile_instrument_evidence("US0378331006", MIC, (record("a"), record("b")))
        self.assertEqual(r["blocks"], ["INVALID_ISIN"])

    def test_bad_evidence_isin_blocks(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (record("a", isin="US0378331006"), record("b")))
        self.assertEqual(r["blocks"], ["INVALID_EVIDENCE_IDENTIFIER"])

    def test_malformed_record_blocks(self):
        r = reconcile_instrument_evidence(ISIN, MIC, (None, record("b")))
        self.assertEqual(r["blocks"], ["INVALID_EVIDENCE_RECORD"])


if __name__ == "__main__":
    unittest.main()
