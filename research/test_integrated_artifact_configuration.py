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

if __name__ == "__main__":
    unittest.main()
