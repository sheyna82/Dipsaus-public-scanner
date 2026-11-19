import io
import unittest
import zipfile
import warnings
from research.spoor2_iso_mic_xlsx_intake_20261113 import inspect_iso_mic_xlsx


def workbook(*, xml=None, duplicate=False, unsafe=False):
    if xml is None:
        xml = b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", b"<Types/>")
        z.writestr("xl/workbook.xml", xml)
        if duplicate:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Duplicate name:", category=UserWarning)
                z.writestr("xl/workbook.xml", xml)
        if unsafe:
            z.writestr("../unsafe", b"x")
    return buf.getvalue()


class IsoMicXlsxIntakeTests(unittest.TestCase):
    def test_valid_container_never_attests_origin(self):
        r = inspect_iso_mic_xlsx(workbook())
        self.assertTrue(r["xlsx_container_valid"])
        self.assertEqual(len(r["sha256"]), 64)
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["mic_registered"])
        self.assertFalse(r["order_placement_enabled"])

    def test_random_bytes_rejected(self):
        self.assertIn("INVALID_XLSX_CONTAINER",
                      inspect_iso_mic_xlsx(b"not a zip")["blocks"])

    def test_empty_rejected(self):
        self.assertIn("INVALID_OR_OVERSIZED_DATASET",
                      inspect_iso_mic_xlsx(b"")["blocks"])

    def test_duplicate_zip_members_rejected(self):
        self.assertIn("DUPLICATE_OR_EXCESSIVE_ZIP_MEMBERS",
                      inspect_iso_mic_xlsx(workbook(duplicate=True))["blocks"])

    def test_zip_traversal_rejected(self):
        self.assertIn("UNSAFE_ZIP_MEMBER_PATH",
                      inspect_iso_mic_xlsx(workbook(unsafe=True))["blocks"])

    def test_xml_entity_rejected(self):
        xml = b'<!DOCTYPE x [<!ENTITY y "z">]><workbook/>'
        self.assertIn("UNSAFE_WORKBOOK_XML",
                      inspect_iso_mic_xlsx(workbook(xml=xml))["blocks"])

    def test_wrong_xml_root_rejected(self):
        self.assertIn("INVALID_WORKBOOK_ROOT",
                      inspect_iso_mic_xlsx(workbook(xml=b"<notworkbook/>"))["blocks"])

    def test_oversized_dataset_rejected_before_parsing(self):
        from research.spoor2_iso_mic_xlsx_intake_20261113 import MAX_BYTES
        self.assertIn("INVALID_OR_OVERSIZED_DATASET",
                      inspect_iso_mic_xlsx(b"x" * (MAX_BYTES + 1))["blocks"])

    def test_missing_workbook_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("[Content_Types].xml", b"<Types/>")
        self.assertIn("NOT_AN_XLSX_WORKBOOK",
                      inspect_iso_mic_xlsx(buf.getvalue())["blocks"])

    def test_same_bytes_same_digest(self):
        payload = workbook()
        self.assertEqual(inspect_iso_mic_xlsx(payload)["sha256"],
                         inspect_iso_mic_xlsx(payload)["sha256"])
