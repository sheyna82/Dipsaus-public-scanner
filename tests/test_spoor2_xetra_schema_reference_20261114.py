"""Synthetic schema evidence only; no claimed official Xetra header."""
import hashlib
import json
import unittest
from research.spoor2_xetra_schema_reference_20261114 import compare_xetra_csv_schema

HEADER = ("ISIN", "MIC")
FINGERPRINT = hashlib.sha256(
    json.dumps(HEADER, ensure_ascii=False, separators=(",", ":")).encode()
).hexdigest()


class XetraSchemaReferenceTests(unittest.TestCase):
    def test_missing_reference_blocks(self):
        r = compare_xetra_csv_schema(b"ISIN,MIC\na,b\n")
        self.assertEqual(r["blocks"], ["REVIEWED_SCHEMA_REQUIRED"])

    def test_exact_synthetic_schema_is_still_blocked(self):
        r = compare_xetra_csv_schema(b"ISIN,MIC\na,b\n", HEADER, FINGERPRINT)
        self.assertTrue(r["schema_matches_reviewed_reference"])
        self.assertEqual(r["row_count"], 1)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["instrument_segment_verified"])
        self.assertFalse(r["broker_route_verified"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])

    def test_schema_mismatch_blocks(self):
        r = compare_xetra_csv_schema(b"MIC,ISIN\na,b\n", HEADER, FINGERPRINT)
        self.assertEqual(r["blocks"], ["CSV_SCHEMA_MISMATCH"])

    def test_bad_reference_hash_blocks(self):
        r = compare_xetra_csv_schema(b"ISIN,MIC\na,b\n", HEADER, "0" * 64)
        self.assertEqual(r["blocks"], ["REVIEWED_REFERENCE_HASH_MISMATCH"])

    def test_duplicate_reference_fields_block(self):
        r = compare_xetra_csv_schema(b"ISIN,MIC\na,b\n", ("ISIN", "ISIN"), FINGERPRINT)
        self.assertEqual(r["blocks"], ["REVIEWED_SCHEMA_REQUIRED"])

    def test_row_width_mismatch_blocks(self):
        r = compare_xetra_csv_schema(b"ISIN,MIC\na,b,c\n", HEADER, FINGERPRINT)
        self.assertEqual(r["blocks"], ["CSV_ROW_WIDTH_MISMATCH"])

    def test_header_without_data_blocks(self):
        r = compare_xetra_csv_schema(b"ISIN,MIC\n", HEADER, FINGERPRINT)
        self.assertEqual(r["blocks"], ["CSV_NO_DATA_ROWS"])

    def test_malformed_csv_blocks(self):
        r = compare_xetra_csv_schema(b'ISIN,MIC\n"unterminated,b\n', HEADER, FINGERPRINT)
        self.assertEqual(r["blocks"], ["CSV_PARSE_ERROR"])


if __name__ == "__main__":
    unittest.main()
