"""Synthetic source-to-MIC import handoff tests."""
import hashlib
import unittest
from datetime import date
from research_mic_import import validate_mic_snapshot

URL = "https://www.iso20022.org/market-identifier-codes"
BODY = b"Code,Kind,Parent,State\nXETR,OPRT,,ACTIVE\nXETA,SGMT,XETR,ACTIVE\n"
COLS = {"mic": "Code", "kind": "Kind", "operating_mic": "Parent", "status": "State"}


class ImportTests(unittest.TestCase):
    def check(self, **updates):
        args = {"body": BODY, "source_url": URL, "approved_url": URL,
                "response_status": 200,
                "expected_sha256": hashlib.sha256(BODY).hexdigest(),
                "columns": COLS, "publication_date": date(2026, 11, 9),
                "effective_date": date(2026, 11, 23),
                "as_of": date(2026, 11, 24)}
        args.update(updates)
        return validate_mic_snapshot(**args)

    def test_consistent_metadata_still_unverified(self):
        r = self.check()
        self.assertEqual(r["status"], "OFFLINE_MIC_IMPORT_CONSISTENT")
        self.assertFalse(r["source_authenticity_independently_verified"])
        self.assertFalse(r["trade_ready"])

    def test_wrong_url(self):
        self.assertEqual(self.check(source_url="https://example.org")["source_reason"], "UNAPPROVED_SOURCE_URL")

    def test_redirect(self):
        self.assertEqual(self.check(response_status=302)["source_reason"], "HTTP_STATUS_NOT_OK")

    def test_digest_mismatch(self):
        self.assertEqual(self.check(expected_sha256="0"*64)["source_reason"], "DIGEST_NOT_ATTESTED")

    def test_bad_encoding(self):
        body = b"\xff\xfe"
        self.assertEqual(self.check(body=body, expected_sha256=hashlib.sha256(body).hexdigest())["reason"], "INVALID_ENCODING")

    def test_unexpected_headers(self):
        self.assertEqual(self.check(columns={**COLS, "mic": "Unknown"})["parser_reason"], "HEADER_MISMATCH")

    def test_future_effective_date(self):
        self.assertEqual(self.check(as_of=date(2026, 11, 19))["parser_reason"], "NOT_YET_EFFECTIVE")

    def test_missing_parent(self):
        body = b"Code,Kind,Parent,State\nXETA,SGMT,XETR,ACTIVE\n"
        self.assertEqual(self.check(body=body, expected_sha256=hashlib.sha256(body).hexdigest())["parser_reason"], "SEGMENT_PARENT_UNVERIFIED")

    def test_bom_input(self):
        body = b"\xef\xbb\xbf" + BODY
        r = self.check(body=body, expected_sha256=hashlib.sha256(body).hexdigest())
        self.assertEqual(r["status"], "OFFLINE_MIC_IMPORT_CONSISTENT")

    def test_extra_fields_not_allowed_by_csv_parser(self):
        body = BODY + b"XAMS,OPRT,,ACTIVE,EXTRA\n"
        self.assertEqual(self.check(body=body, expected_sha256=hashlib.sha256(body).hexdigest())["parser_reason"], "ROW_SHAPE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
