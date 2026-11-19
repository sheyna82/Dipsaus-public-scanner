"""Fail-closed offline capture reconstruction tests. No external network."""
import base64
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from research_rebuild_omxh25_archive import rebuild, CAPTURE_MEMBERS


class Tests(unittest.TestCase):
    def capture(self, path, *, trade_ready=False, extra=False):
        with zipfile.ZipFile(path, "w") as archive:
            for source in CAPTURE_MEMBERS:
                raw = b"%PDF-1.7\nnot-an-official-pdf"
                archive.writestr(source, json.dumps({
                    "official_document_base64": base64.b64encode(raw).decode(),
                    "official_document_sha256": hashlib.sha256(raw).hexdigest(),
                    "research_only": True,
                    "trade_ready": trade_ready,
                    "independently_audited": False,
                }))
            if extra:
                archive.writestr("unexpected.txt", "untrusted")

    def test_synthetic_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d)/"capture.zip", Path(d)/"derived.zip"
            self.capture(src)
            with self.assertRaisesRegex(ValueError, "CAPTURE_PDF_HASH_MISMATCH"):
                rebuild(src, dst)
            self.assertFalse(dst.exists())

    def test_trade_promotion_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d)/"capture.zip", Path(d)/"derived.zip"
            self.capture(src, trade_ready=True)
            with self.assertRaisesRegex(ValueError, "CAPTURE_RESEARCH_CONTRACT_INVALID"):
                rebuild(src, dst)

    def test_extra_capture_member_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d)/"capture.zip", Path(d)/"derived.zip"
            self.capture(src, extra=True)
            with self.assertRaisesRegex(ValueError, "CAPTURE_MEMBERS_INVALID"):
                rebuild(src, dst)

    def test_artifact_digest_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d)/"capture.zip", Path(d)/"derived.zip"
            self.capture(src)
            with self.assertRaisesRegex(ValueError, "CAPTURE_ARTIFACT_HASH_MISMATCH"):
                rebuild(src, dst, "0"*64)

    def test_no_in_place_replacement(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d)/"capture.zip"
            self.capture(src)
            with self.assertRaisesRegex(ValueError, "INPUT_OUTPUT_SAME_PATH"):
                rebuild(src, src)


if __name__ == "__main__":
    unittest.main()
