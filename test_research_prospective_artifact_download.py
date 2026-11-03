import io
import hashlib
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from research_prospective_archive import archive_ledger
from research_prospective_artifact_download import download_previous_archive


class Response(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class ArtifactDownloadTests(unittest.TestCase):
    def test_download_and_verify_nested_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "candidates", root / "outcomes"
            a.mkdir()
            b.mkdir()
            (a / "sample.json").write_text('{"research_only": true}')
            archive = root / "inner.zip"
            archive_ledger(a, b, archive)
            outer = io.BytesIO()
            with ZipFile(outer, "w") as z:
                z.writestr("synthetic-prospective-ledger.zip", archive.read_bytes())
            dest = root / "restored.zip"
            result = download_previous_archive(
                "owner/repo", "fake-token", 42, dest,
                opener=lambda request, timeout: Response(outer.getvalue()))
            self.assertEqual(result["verified_files"], 1)
            with self.assertRaises(FileExistsError):
                download_previous_archive(
                    "owner/repo", "fake-token", 42, dest,
                    opener=lambda request, timeout: Response(outer.getvalue()))

    def test_reject_unexpected_outer_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            outer = io.BytesIO()
            with ZipFile(outer, "w") as z:
                z.writestr("unexpected.txt", "no")
            dest = Path(tmp) / "archive.zip"
            with self.assertRaisesRegex(ValueError, "unexpected_outer_artifact_contents"):
                download_previous_archive(
                    "owner/repo", "fake-token", 42, dest,
                    opener=lambda request, timeout: Response(outer.getvalue()))
            self.assertFalse(dest.exists())


    def test_pinned_digest_accepts_match_and_rejects_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "candidates", root / "outcomes"
            a.mkdir()
            b.mkdir()
            (a / "sample.json").write_text('{"synthetic_data_only": true}')
            inner_path = root / "source.zip"
            archive_ledger(a, b, inner_path)
            raw = inner_path.read_bytes()
            outer = io.BytesIO()
            with ZipFile(outer, "w") as z:
                z.writestr("synthetic-prospective-ledger.zip", raw)
            digest = hashlib.sha256(raw).hexdigest()
            ok = download_previous_archive(
                "owner/repo", "fake-token", 42, root / "ok.zip",
                expected_sha256=digest,
                opener=lambda request, timeout: Response(outer.getvalue()))
            self.assertTrue(ok["expected_sha256_verified"])
            self.assertEqual(ok["sha256"], digest)
            blocked = root / "blocked.zip"
            with self.assertRaisesRegex(ValueError, "artifact_expected_sha256_mismatch"):
                download_previous_archive(
                    "owner/repo", "fake-token", 42, blocked,
                    expected_sha256="0" * 64,
                    opener=lambda request, timeout: Response(outer.getvalue()))
            self.assertFalse(blocked.exists())
            with self.assertRaisesRegex(ValueError, "invalid_expected_sha256"):
                download_previous_archive(
                    "owner/repo", "fake-token", 42, blocked,
                    expected_sha256="bad",
                    opener=lambda request, timeout: Response(outer.getvalue()))

if __name__ == "__main__":
    unittest.main()
