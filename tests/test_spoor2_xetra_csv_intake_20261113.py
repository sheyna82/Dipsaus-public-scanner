import unittest
from research.spoor2_xetra_csv_intake_20261113 import inspect_xetra_csv


class XetraCsvIntakeTests(unittest.TestCase):
    def test_valid_csv_still_not_attested(self):
        r = inspect_xetra_csv(b"ISIN,Segment\nDE0006231004,XETA\nDE0007030009,XETB\n")
        self.assertTrue(r["csv_syntax_valid"])
        self.assertEqual(r["row_count"], 2)
        self.assertFalse(r["instrument_segment_verified"])
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])
        self.assertIn("ORIGINAL_XETRA_SOURCE_NOT_ATTESTED", r["blocks"])

    def test_invalid_bytes(self):
        self.assertIn("INVALID_OR_OVERSIZED_XETRA_CSV", inspect_xetra_csv(None)["blocks"])

    def test_duplicate_header(self):
        self.assertIn("INVALID_XETRA_CSV_HEADER", inspect_xetra_csv(b"ISIN,ISIN\na,b\n")["blocks"])

    def test_column_mismatch(self):
        self.assertIn("INCONSISTENT_XETRA_CSV_COLUMNS", inspect_xetra_csv(b"a,b\n1\n")["blocks"])

    def test_null_byte(self):
        self.assertIn("NUL_BYTE_IN_XETRA_CSV", inspect_xetra_csv(b"a,b\n1,\x002\n")["blocks"])

    def test_empty_rows(self):
        self.assertIn("EMPTY_XETRA_CSV", inspect_xetra_csv(b"a,b\n")["blocks"])
