import io
import unittest
import zipfile

from research.spoor2_xetra_zip_intake_20261113 import inspect_xetra_static_zip


def make_zip(names):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        for name, payload in names:
            archive.writestr(name, payload)
    return buf.getvalue()


class XetraZipIntakeTests(unittest.TestCase):
    def test_valid_zip_still_not_attested(self):
        result = inspect_xetra_static_zip(make_zip([("static.csv", b"ISIN\nDE0006231004\n")]))
        self.assertTrue(result["zip_container_valid"])
        self.assertEqual(result["member_count"], 1)
        self.assertFalse(result["source_attested"])
        self.assertFalse(result["instrument_segment_verified"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["order_placement_enabled"])

    def test_invalid_payload(self):
        self.assertIn("INVALID_OR_OVERSIZED_XETRA_ZIP",
                      inspect_xetra_static_zip(b"")["blocks"])

    def test_non_zip(self):
        self.assertIn("INVALID_XETRA_ZIP_CONTAINER",
                      inspect_xetra_static_zip(b"not a zip")["blocks"])

    def test_traversal(self):
        self.assertIn("UNSAFE_XETRA_ZIP_MEMBER_PATH",
                      inspect_xetra_static_zip(make_zip([("../escape", b"x")]))["blocks"])

    def test_duplicate_members(self):
        self.assertIn("DUPLICATE_OR_EXCESSIVE_XETRA_ZIP_MEMBERS",
                      inspect_xetra_static_zip(make_zip([("x", b"a"), ("x", b"b")]))["blocks"])

    def test_empty_zip(self):
        self.assertIn("DUPLICATE_OR_EXCESSIVE_XETRA_ZIP_MEMBERS",
                      inspect_xetra_static_zip(make_zip([]))["blocks"])
