import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from research_synthetic_transport_verifier import verify_synthetic_artifact_transport
from research_prospective_archive import archive_ledger


class SyntheticTransportVerifierTests(unittest.TestCase):
    def make_payload(self, *, corrupt=False):
        root = Path(self.tmp.name)
        (root / "candidates").mkdir(exist_ok=True)
        (root / "outcomes").mkdir(exist_ok=True)
        inner = root / "inner.zip"
        if inner.exists():
            inner.unlink()
        archive_ledger(root / "candidates", root / "outcomes", inner)
        raw = inner.read_bytes()
        digest = ("0" * 64) if corrupt else hashlib.sha256(raw).hexdigest()
        stream = io.BytesIO()
        with ZipFile(stream, "w") as outer:
            outer.writestr("prospective-ledger-synthetic.zip", raw)
            outer.writestr("sha256.txt", digest + "  prospective-ledger-synthetic.zip\n")
        return stream.getvalue()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_two_member_envelope_and_manifest(self):
        dest = Path(self.tmp.name) / "restored.zip"
        result = verify_synthetic_artifact_transport(self.make_payload(), dest)
        self.assertTrue(result["inner_manifest_verified"])
        self.assertFalse(result["external_github_artifact_digest_verified"])
        self.assertEqual(result["registered_stock_candidates"], 0)

    def test_bad_inner_digest_rejected(self):
        dest = Path(self.tmp.name) / "restored.zip"
        with self.assertRaisesRegex(ValueError, "inner_archive_checksum_mismatch"):
            verify_synthetic_artifact_transport(self.make_payload(corrupt=True), dest)
        self.assertFalse(dest.exists())

    def test_extra_member_rejected(self):
        payload = self.make_payload()
        stream = io.BytesIO()
        with ZipFile(io.BytesIO(payload)) as original, ZipFile(stream, "w") as outer:
            for name in original.namelist():
                outer.writestr(name, original.read(name))
            outer.writestr("unexpected.txt", "bad")
        with self.assertRaisesRegex(ValueError, "unexpected_artifact_members"):
            verify_synthetic_artifact_transport(stream.getvalue(), Path(self.tmp.name) / "restored.zip")


if __name__ == "__main__":
    unittest.main()
