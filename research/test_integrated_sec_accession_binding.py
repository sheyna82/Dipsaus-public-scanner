"""Synthetic SEC accession binding fixtures."""
import unittest
from integrated_sec_accession_binding import verify_sec_accession_binding

ACCESSION = "0000123456-26-000001"
URL = ("https://www.sec.gov/Archives/edgar/data/123456/"
       "000012345626000001/0000123456-26-000001.txt")
RAW = b"<SEC-HEADER>\n<ACCESSION-NUMBER>0000123456-26-000001\n</SEC-HEADER>\n"


class SecAccessionBindingTests(unittest.TestCase):
    def test_consistent_document_does_not_prove_authenticity(self):
        result = verify_sec_accession_binding(RAW, URL)
        self.assertTrue(result["internal_accession_consistency"])
        self.assertFalse(result["source_bytes_authenticity_independently_proven"])
        self.assertFalse(result["public_dissemination_time_independently_proven"])

    def test_wrong_url_accession_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SEC_ACCESSION_URL_MISMATCH"):
            verify_sec_accession_binding(
                RAW, URL.replace("0000123456-26-000001.txt", "0000123456-26-000002.txt"))

    def test_wrong_directory_accession_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SEC_ACCESSION_URL_MISMATCH"):
            verify_sec_accession_binding(
                RAW, URL.replace("000012345626000001/", "000012345626000002/"))

    def test_missing_or_duplicate_accession_fails_closed(self):
        for raw in (b"no accession", RAW + RAW):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(ValueError, "MISSING_OR_AMBIGUOUS_SEC_ACCESSION"):
                    verify_sec_accession_binding(raw, URL)

    def test_noncanonical_or_untrusted_url_rejected(self):
        for url in (URL.replace("www.sec.gov", "www.sec.gov.evil.example"),
                    URL.replace("https:", "http:"),
                    URL + "?redirect=1",
                    URL.replace("/0000123456-26-000001.txt", "/filing.htm")):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    verify_sec_accession_binding(RAW, url)


if __name__ == "__main__":
    unittest.main()
