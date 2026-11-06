"""Synthetic SEC EDGAR header fixtures; no live SEC authenticity claims."""
import unittest
from integrated_sec_acceptance_evidence import inspect_sec_acceptance_header

URL = "https://www.sec.gov/Archives/edgar/data/123456/000012345626000001/filing.txt"
RAW = b"<SEC-HEADER>\n<ACCEPTANCE-DATETIME>20261105163000\n</SEC-HEADER>\n"
ENTRY = "2026-11-06T09:00:00-05:00"


class SecAcceptanceEvidenceTests(unittest.TestCase):
    def test_acceptance_parsed_without_dissemination_promotion(self):
        result = inspect_sec_acceptance_header(RAW, URL, ENTRY)
        self.assertEqual(result["acceptance_at_et"], "2026-11-05T16:30:00-05:00")
        self.assertFalse(result["public_dissemination_time_independently_proven"])
        self.assertFalse(result["source_bytes_authenticity_independently_proven"])
        self.assertFalse(result["trade_ready"])

    def test_after_entry_rejected(self):
        with self.assertRaisesRegex(ValueError, "SEC_ACCEPTANCE_NOT_BEFORE_ENTRY"):
            inspect_sec_acceptance_header(RAW, URL, "2026-11-05T16:00:00-05:00")

    def test_missing_and_ambiguous_header_rejected(self):
        for raw in (b"no acceptance header", RAW + RAW):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(ValueError, "MISSING_OR_AMBIGUOUS_SEC_ACCEPTANCE_TIME"):
                    inspect_sec_acceptance_header(raw, URL, ENTRY)

    def test_untrusted_url_rejected(self):
        for url in ("https://evil.example/Archives/edgar/data/x",
                    "http://www.sec.gov/Archives/edgar/data/x",
                    "https://www.sec.gov.evil.example/Archives/edgar/data/x"):
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "INVALID_SEC_ARCHIVE_URL"):
                    inspect_sec_acceptance_header(RAW, url, ENTRY)


if __name__ == "__main__":
    unittest.main()
