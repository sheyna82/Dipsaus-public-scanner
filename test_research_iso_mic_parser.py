"""Synthetic offline MIC CSV tests; fixtures are NOT the official ISO file."""
import hashlib
import unittest
from datetime import date
from research_iso_mic_parser import parse_mic_csv

CSV = "Code,Kind,Parent,State\nXETR,OPRT,,ACTIVE\nXETS,SGMT,XETR,ACTIVE\n"
COLUMNS = {"mic": "Code", "kind": "Kind", "operating_mic": "Parent", "status": "State"}
PUB = date(2026, 11, 9)
EFF = date(2026, 11, 23)


class MicTests(unittest.TestCase):
    def check(self, csv_text=CSV, **changes):
        args = dict(columns=COLUMNS, publication_date=PUB, effective_date=EFF,
                    as_of=date(2026, 11, 24),
                    expected_sha256=hashlib.sha256(csv_text.encode()).hexdigest())
        args.update(changes)
        return parse_mic_csv(csv_text, **args)

    def test_valid_synthetic_register_non_executable(self):
        r = self.check()
        self.assertEqual(r["status"], "OFFLINE_MIC_SCHEMA_VALIDATED")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["source_authenticity_independently_verified"])

    def test_future_effective_date_blocked(self):
        self.assertEqual(self.check(as_of=date(2026, 11, 19))["reason"], "NOT_YET_EFFECTIVE")

    def test_no_digest_blocked(self):
        self.assertEqual(self.check(expected_sha256=None)["reason"], "UNATTESTED_SOURCE_DIGEST")

    def test_bad_digest_blocked(self):
        self.assertEqual(self.check(expected_sha256="0"*64)["reason"], "SOURCE_DIGEST_MISMATCH")

    def test_missing_schema_blocked(self):
        self.assertEqual(self.check(columns={})["reason"], "SCHEMA_NOT_DECLARED")

    def test_header_mismatch_blocked(self):
        self.assertEqual(self.check(columns={**COLUMNS, "mic": "Wrong"})["reason"], "HEADER_MISMATCH")

    def test_duplicate_mic_blocked(self):
        self.assertEqual(self.check(CSV+"XETR,OPRT,,ACTIVE\n")["reason"], "DUPLICATE_MIC")

    def test_missing_segment_parent_blocked(self):
        self.assertEqual(self.check(CSV.replace("XETR,OPRT,,ACTIVE\n", ""))["reason"], "SEGMENT_PARENT_UNVERIFIED")

    def test_inactive_parent_blocked(self):
        self.assertEqual(self.check(CSV.replace("XETR,OPRT,,ACTIVE", "XETR,OPRT,,INACTIVE"))["reason"], "SEGMENT_PARENT_UNVERIFIED")

    def test_unknown_status_blocked(self):
        self.assertEqual(self.check(CSV.replace("ACTIVE", "SOMETHING", 1))["reason"], "UNRECOGNIZED_SOURCE_VALUE")

    def test_duplicate_headers_blocked(self):
        self.assertEqual(self.check("Code,Kind,Parent,Code\nXETR,OPRT,,ACTIVE\n")["reason"], "HEADER_MISMATCH")

    def test_publication_in_future_blocked(self):
        self.assertEqual(self.check(as_of=date(2026, 11, 1))["reason"], "INVALID_PUBLICATION_TIMELINE")


if __name__ == "__main__":
    unittest.main()
