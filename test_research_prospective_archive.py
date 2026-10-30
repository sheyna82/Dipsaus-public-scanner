import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from research_prospective_archive import archive_ledger, verify_archive


class ProspectiveArchiveTests(unittest.TestCase):
    def test_snapshot_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates, outcomes = root / "candidates", root / "outcomes"
            candidates.mkdir()
            outcomes.mkdir()
            (candidates / "a.json").write_text(json.dumps({"signal": True}))
            (outcomes / "b.json").write_text(json.dumps({"outcome": 1}))
            path = root / "snapshot.zip"
            result = archive_ledger(candidates, outcomes, path)
            self.assertEqual(result["entry_count"], 2)
            self.assertTrue(verify_archive(path)["valid"])
            with self.assertRaises(FileExistsError):
                archive_ledger(candidates, outcomes, path)
            with ZipFile(path, "a", compression=ZIP_DEFLATED) as archive:
                archive.writestr("untracked.json", "{}")
            with self.assertRaisesRegex(ValueError, "unexpected_archive_member"):
                verify_archive(path)


if __name__ == "__main__":
    unittest.main()
