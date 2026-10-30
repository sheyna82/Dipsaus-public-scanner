import tempfile
import unittest
from pathlib import Path
from research_prospective_archive import archive_ledger
from research_prospective_archive_restore import restore_archive


class RestoreArchiveTests(unittest.TestCase):
    def test_round_trip_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "candidates", root / "outcomes"
            a.mkdir()
            b.mkdir()
            (a / "signal.json").write_text('{"signal": true}')
            (b / "outcome.json").write_text('{"outcome": 1}')
            archive = root / "ledger.zip"
            archive_ledger(a, b, archive)
            target = root / "restored"
            result = restore_archive(archive, target)
            self.assertEqual(result["restored_files"], 2)
            self.assertEqual((target / "candidates" / "signal.json").read_bytes(),
                             (a / "signal.json").read_bytes())
            with self.assertRaisesRegex(ValueError, "destination_not_empty"):
                restore_archive(archive, target)


if __name__ == "__main__":
    unittest.main()
