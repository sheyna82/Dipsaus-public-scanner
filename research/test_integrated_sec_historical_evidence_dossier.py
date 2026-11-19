"""Synthetic historical SEC dossier regression tests."""
import copy
import unittest
from integrated_sec_historical_evidence_dossier import (
    build_sec_historical_evidence_dossier, verify_sec_historical_evidence_dossier,
)

URL = ("https://www.sec.gov/Archives/edgar/data/123456/"
       "000012345626000001/0000123456-26-000001.txt")
RAW = (b"<SEC-HEADER>\n<ACCESSION-NUMBER>0000123456-26-000001\n"
       b"<ACCEPTANCE-DATETIME>20261105163000\n</SEC-HEADER>\n")
ENTRY = "2026-11-06T09:00:00-05:00"


class HistoricalSecDossierTests(unittest.TestCase):
    def test_dossier_is_deterministic_and_not_trade_ready(self):
        a = build_sec_historical_evidence_dossier("candidate-001", RAW, URL, ENTRY)
        b = build_sec_historical_evidence_dossier("candidate-001", RAW, URL, ENTRY)
        self.assertEqual(a, b)
        self.assertTrue(verify_sec_historical_evidence_dossier(a))
        self.assertFalse(a["dossier"]["historical_publication_proven"])
        self.assertFalse(a["dossier"]["eligible_for_backtest_performance_claim"])

    def test_modified_dossier_fails_hash(self):
        a = build_sec_historical_evidence_dossier("candidate-001", RAW, URL, ENTRY)
        a["dossier"]["candidate_id"] = "different"
        with self.assertRaisesRegex(ValueError, "SEC_DOSSIER_HASH_MISMATCH"):
            verify_sec_historical_evidence_dossier(a)

    def test_rehashed_false_claim_is_rejected(self):
        import hashlib
        import json
        a = build_sec_historical_evidence_dossier("candidate-001", RAW, URL, ENTRY)
        a["dossier"]["historical_publication_proven"] = True
        canonical = json.dumps(a["dossier"], sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        a["dossier_sha256"] = hashlib.sha256(canonical.encode("ascii")).hexdigest()
        with self.assertRaisesRegex(ValueError, "SEC_DOSSIER_UNSUPPORTED_EVIDENCE_PROMOTION"):
            verify_sec_historical_evidence_dossier(a)

    def test_post_entry_retrieval_recorded_but_never_promoted(self):
        bundle = build_sec_historical_evidence_dossier(
            "candidate-001", RAW, URL, ENTRY,
            retrieved_at="2026-11-07T12:00:00Z",
            claimed_public_at="2026-11-05T20:00:00Z")
        self.assertTrue(verify_sec_historical_evidence_dossier(bundle))
        chronology = bundle["dossier"]["source_chronology"]
        self.assertFalse(chronology["retrieval_precedes_entry"])
        self.assertFalse(chronology["historical_publication_independently_proven"])

    def test_rehashed_chronology_promotion_rejected(self):
        import hashlib
        import json
        bundle = build_sec_historical_evidence_dossier(
            "candidate-001", RAW, URL, ENTRY,
            retrieved_at="2026-11-05T20:00:00Z")
        bundle["dossier"]["source_chronology"]["historical_publication_independently_proven"] = True
        canonical = json.dumps(bundle["dossier"], sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        bundle["dossier_sha256"] = hashlib.sha256(canonical.encode("ascii")).hexdigest()
        with self.assertRaisesRegex(ValueError, "SEC_DOSSIER_UNSUPPORTED_CHRONOLOGY_PROMOTION"):
            verify_sec_historical_evidence_dossier(bundle)

    def test_missing_accession_and_bad_candidate_rejected(self):
        with self.assertRaises(ValueError):
            build_sec_historical_evidence_dossier("", RAW, URL, ENTRY)
        with self.assertRaisesRegex(ValueError, "MISSING_OR_AMBIGUOUS_SEC_ACCESSION"):
            build_sec_historical_evidence_dossier("candidate-001", b"invalid", URL, ENTRY)


if __name__ == "__main__":
    unittest.main()
