"""Isolated offline tests: synthetic bytes only, no network access."""
import io
import unittest
import zipfile
from unittest.mock import patch

from research.spoor2_xetra_offline_structure_20261114 import inspect_xetra_bytes


def make_zip(name="data.xml", content=b"<x/>"):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(name, content)
    return output.getvalue()


class XetraOfflineStructureTests(unittest.TestCase):
    def test_csv_valid_structure_is_not_attested(self):
        result = inspect_xetra_bytes("csv", b"ISIN,MIC\nDE0000000001,XETR\n")
        self.assertTrue(result["format_plausible"])
        for key in ("source_attested", "instrument_segment_verified",
                    "broker_route_verified", "trade_ready", "order_placement_enabled"):
            self.assertFalse(result[key])

    def test_csv_invalid_utf8_blocks(self):
        self.assertFalse(inspect_xetra_bytes("csv", b"\xff,abc")["format_plausible"])

    def test_csv_nul_blocks(self):
        self.assertFalse(inspect_xetra_bytes("csv", b"a,b\n\x00,c")["format_plausible"])

    def test_csv_one_column_blocks(self):
        self.assertFalse(inspect_xetra_bytes("csv", b"onlyone\n")["format_plausible"])

    def test_zip_valid_structure_is_not_attested(self):
        result = inspect_xetra_bytes("zip", make_zip())
        self.assertTrue(result["format_plausible"])
        self.assertFalse(result["source_attested"])
        self.assertFalse(result["trade_ready"])

    def test_zip_invalid_bytes_blocks(self):
        self.assertFalse(inspect_xetra_bytes("zip", b"not a zip")["format_plausible"])

    def test_zip_traversal_blocks(self):
        result = inspect_xetra_bytes("zip", make_zip("../bad.xml"))
        self.assertEqual(result["blocks"], ["ZIP_UNSAFE_MEMBER"])

    def test_zip_absolute_path_blocks(self):
        result = inspect_xetra_bytes("zip", make_zip("/bad.xml"))
        self.assertEqual(result["blocks"], ["ZIP_UNSAFE_MEMBER"])

    def test_zip_uncompressed_limit_blocks(self):
        with patch("research.spoor2_xetra_offline_structure_20261114.MAX_UNCOMPRESSED", 3):
            result = inspect_xetra_bytes("zip", make_zip(content=b"1234"))
        self.assertEqual(result["blocks"], ["ZIP_UNCOMPRESSED_SIZE_LIMIT"])

    def test_zip_member_count_limit_blocks(self):
        with patch("research.spoor2_xetra_offline_structure_20261114.MAX_MEMBERS", 0):
            result = inspect_xetra_bytes("zip", make_zip())
        self.assertEqual(result["blocks"], ["ZIP_MEMBER_COUNT"])

    def test_invalid_inputs_block(self):
        for kind, data in (("csv", b""), ("unknown", b"a,b"), ("zip", None)):
            self.assertFalse(inspect_xetra_bytes(kind, data)["trade_ready"])
            self.assertFalse(inspect_xetra_bytes(kind, data)["format_plausible"])


if __name__ == "__main__":
    unittest.main()
