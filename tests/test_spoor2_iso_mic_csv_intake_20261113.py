import unittest
from research.spoor2_iso_mic_csv_intake_20261113 import inspect_iso_mic_csv, MAX_CSV_BYTES


class IsoMicCsvIntakeTests(unittest.TestCase):
    def test_valid_csv_never_attests_origin(self):
        r = inspect_iso_mic_csv(b"MIC,COUNTRY\nXAMS,NL\n")
        self.assertTrue(r["csv_syntax_valid"])
        self.assertEqual(r["row_count"], 1)
        self.assertEqual(len(r["sha256"]), 64)
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["mic_registered"])
        self.assertFalse(r["trade_ready"])

    def test_empty_input_rejected(self):
        self.assertIn("INVALID_OR_OVERSIZED_CSV",
                      inspect_iso_mic_csv(b"")["blocks"])

    def test_oversized_input_rejected(self):
        self.assertIn("INVALID_OR_OVERSIZED_CSV",
                      inspect_iso_mic_csv(b"x" * (MAX_CSV_BYTES + 1))["blocks"])

    def test_invalid_utf8_rejected(self):
        self.assertIn("INVALID_CSV_ENCODING_OR_SYNTAX",
                      inspect_iso_mic_csv(b"MIC\n\xff")["blocks"])

    def test_nul_rejected(self):
        self.assertIn("NUL_BYTE_IN_CSV",
                      inspect_iso_mic_csv(b"MIC\nX\x00AMS")["blocks"])

    def test_duplicate_headers_rejected(self):
        self.assertIn("INVALID_CSV_HEADER",
                      inspect_iso_mic_csv(b"MIC,MIC\nXAMS,XAMS\n")["blocks"])

    def test_missing_data_rows_rejected(self):
        self.assertIn("NO_CSV_DATA_ROWS",
                      inspect_iso_mic_csv(b"MIC,COUNTRY\n")["blocks"])

    def test_inconsistent_columns_rejected(self):
        self.assertIn("INCONSISTENT_CSV_COLUMNS",
                      inspect_iso_mic_csv(b"MIC,COUNTRY\nXAMS\n")["blocks"])

    def test_unclosed_quote_rejected(self):
        self.assertIn("INVALID_CSV_ENCODING_OR_SYNTAX",
                      inspect_iso_mic_csv(b'MIC,COUNTRY\n"XAMS,NL\n')["blocks"])

    def test_utf8_bom_accepted_but_unattested(self):
        r = inspect_iso_mic_csv(b"\xef\xbb\xbfMIC,COUNTRY\nXAMS,NL\n")
        self.assertTrue(r["csv_syntax_valid"])
        self.assertFalse(r["order_placement_enabled"])
