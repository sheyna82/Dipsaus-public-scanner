"""Synthetic unified SEC document audit tests."""
import hashlib
import unittest
from integrated_sec_complete_submission_audit import inspect_sec_complete_submission

URL = ("https://www.sec.gov/Archives/edgar/data/123456/"
       "000012345626000001/0000123456-26-000001.txt")
RAW = (b"<SEC-HEADER>\n<ACCESSION-NUMBER>0000123456-26-000001\n"
       b"<ACCEPTANCE-DATETIME>20261105163000\n</SEC-HEADER>\n")
ENTRY = "2026-11-06T09:00:00-05:00"


class SecCompleteSubmissionAuditTests(unittest.TestCase):
    def test_complete_submission_is_still_not_publication_proof(self):
        result = inspect_sec_complete_submission(RAW, URL, ENTRY)
        self.assertEqual(result["accession"], "0000123456-26-000001")
        self.assertEqual(result["supplied_document_sha256"], hashlib.sha256(RAW).hexdigest())
        self.assertTrue(result["internal_accession_consistency"])
        self.assertFalse(result["public_dissemination_time_independently_proven"])
        self.assertFalse(result["eligible_for_performance_claim"])
        self.assertFalse(result["trade_ready"])

    def test_wrong_accession_fails(self):
        with self.assertRaisesRegex(ValueError, "SEC_ACCESSION_URL_MISMATCH"):
            inspect_sec_complete_submission(RAW.replace(b"0000123456-26-000001",
                                                        b"0000123456-26-000002"), URL, ENTRY)

    def test_future_acceptance_fails(self):
        with self.assertRaisesRegex(ValueError, "SEC_ACCEPTANCE_NOT_BEFORE_ENTRY"):
            inspect_sec_complete_submission(RAW, URL, "2026-11-05T16:00:00-05:00")

    def test_private_to_public_fails(self):
        with self.assertRaisesRegex(ValueError, "SEC_PRIVATE_TO_PUBLIC_ACCEPTANCE_UNUSABLE"):
            inspect_sec_complete_submission(RAW.replace(b"</SEC-HEADER>", b"<PRIVATE-TO-PUBLIC>\n</SEC-HEADER>"), URL, ENTRY)


if __name__ == "__main__":
    unittest.main()
