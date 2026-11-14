"""Offline end-to-end SEC capture pipeline tests; no network."""
import hashlib
import unittest
from datetime import datetime, timezone
from integrated_sec_candidate_capture import capture_sec_candidate

URL = ("https://www.sec.gov/Archives/edgar/data/123456/"
       "000012345626000001/0000123456-26-000001.txt")
RAW = (b"<SEC-HEADER>\n<ACCESSION-NUMBER>0000123456-26-000001\n"
       b"<ACCEPTANCE-DATETIME>20261105163000\n</SEC-HEADER>\n")
ENTRY = "2026-11-06T09:00:00-05:00"


def fake_fetcher(url, agent):
    return RAW, {
        "schema": "sec_live_retrieval_receipt_v1",
        "source_url": url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(RAW).hexdigest(),
        "byte_count": len(RAW),
        "historical_publication_independently_proven": False,
        "eligible_for_performance_claim": False,
        "trade_ready": False,
    }


class SecCandidateCaptureTests(unittest.TestCase):
    def test_end_to_end_receipt_and_dossier_are_bound(self):
        result = capture_sec_candidate("candidate-001", URL, ENTRY, "research test agent", fake_fetcher)
        self.assertEqual(result["retrieval_receipt"]["sha256"],
                         result["evidence_dossier"]["dossier"]["sec_audit"]["supplied_document_sha256"])
        self.assertFalse(result["historical_publication_independently_proven"])
        self.assertFalse(result["eligible_for_backtest_performance_claim"])
        self.assertFalse(result["trade_ready"])

    def test_mismatched_receipt_rejected(self):
        def corrupted(url, agent):
            raw, receipt = fake_fetcher(url, agent)
            receipt["sha256"] = "0" * 64
            return raw, receipt
        with self.assertRaisesRegex(ValueError, "SEC_RETRIEVAL_RECEIPT_MISMATCH"):
            capture_sec_candidate("candidate-001", URL, ENTRY, "research test agent", corrupted)

    def test_false_publication_promotion_rejected(self):
        def promoted(url, agent):
            raw, receipt = fake_fetcher(url, agent)
            receipt["historical_publication_independently_proven"] = True
            return raw, receipt
        with self.assertRaisesRegex(ValueError, "SEC_RETRIEVAL_RECEIPT_MISMATCH"):
            capture_sec_candidate("candidate-001", URL, ENTRY, "research test agent", promoted)


if __name__ == "__main__":
    unittest.main()
