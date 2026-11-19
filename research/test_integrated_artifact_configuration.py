"""Static, offline checks for frozen artifact configuration."""
import unittest
import integrated_artifact_fetch as module

class ArtifactConfigurationTests(unittest.TestCase):
    def test_three_expected_files(self):
        self.assertEqual(len(module.ALLOWED), 3)

    def test_hashes_are_sha256(self):
        self.assertEqual(len(module.ZIP_SHA256), 64)
        for value in module.ALLOWED.values():
            self.assertEqual(len(value), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in value))

    def test_artifact_identity(self):
        self.assertEqual(module.ARTIFACT_ID, 13428010951)


class ArtifactVerificationRegressionTests(unittest.TestCase):
    """Offline adversarial ZIP cases; no network, no trading."""
    def make_zip(self, entries):
        import io
        import zipfile
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as z:
            for name, data in entries:
                z.writestr(name, data)
        return stream.getvalue()

    def verify_with_test_digest(self, raw, allowed):
        import hashlib
        from unittest.mock import patch
        with patch.object(module, "ZIP_SHA256", hashlib.sha256(raw).hexdigest()), patch.object(module, "ALLOWED", allowed):
            return module.verify_zip(raw)

    def test_valid_synthetic_archive(self):
        import hashlib
        payload = b"frozen research"
        allowed = {"a.json": hashlib.sha256(payload).hexdigest()}
        raw = self.make_zip([("a.json", payload)])
        self.assertEqual(self.verify_with_test_digest(raw, allowed), {"a.json": payload})

    def test_zip_digest_mismatch_blocks(self):
        with self.assertRaisesRegex(ValueError, "ARTIFACT_ZIP_HASH_MISMATCH"):
            module.verify_zip(b"tampered")

    def test_member_digest_mismatch_blocks(self):
        raw = self.make_zip([("a.json", b"tampered")])
        with self.assertRaisesRegex(ValueError, "ARTIFACT_FILE_HASH_MISMATCH"):
            self.verify_with_test_digest(raw, {"a.json": "0" * 64})

    def test_missing_member_blocks(self):
        import hashlib
        raw = self.make_zip([("a.json", b"a")])
        allowed = {"a.json": hashlib.sha256(b"a").hexdigest(), "b.json": hashlib.sha256(b"b").hexdigest()}
        with self.assertRaisesRegex(ValueError, "MISSING_ARTIFACT_FILES"):
            self.verify_with_test_digest(raw, allowed)

    def test_unexpected_member_blocks(self):
        import hashlib
        raw = self.make_zip([("a.json", b"a"), ("extra.json", b"x")])
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_ZIP_ENTRY"):
            self.verify_with_test_digest(raw, {"a.json": hashlib.sha256(b"a").hexdigest()})

    def test_duplicate_member_blocks(self):
        import hashlib
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            raw = self.make_zip([("a.json", b"a"), ("a.json", b"a")])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ZIP_ENTRY"):
            self.verify_with_test_digest(raw, {"a.json": hashlib.sha256(b"a").hexdigest()})

    def test_path_traversal_blocks(self):
        import hashlib
        raw = self.make_zip([("../a.json", b"a")])
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_ZIP_ENTRY"):
            self.verify_with_test_digest(raw, {"a.json": hashlib.sha256(b"a").hexdigest()})

    def test_directory_entry_blocks(self):
        raw = self.make_zip([("a.json/", b"")])
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_ZIP_ENTRY"):
            self.verify_with_test_digest(raw, {"a.json": "0" * 64})

    def test_invalid_zip_blocks(self):
        raw = b"not a zip archive"
        with self.assertRaises(Exception):
            self.verify_with_test_digest(raw, {"a.json": "0" * 64})

if __name__ == "__main__":
    unittest.main()
