"""Negative safety tests for portable source backup verification."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from research_verify_omxh25_portable_backup import verify_portable_backup, recover_portable_backup


class PortableBackupTests(unittest.TestCase):
    def make_backup(self, root, manifest=None, receipt=None, original=b"invalid"):
        path = root / "backup.zip"
        manifest = manifest if manifest is not None else {
            "schema": "dipsaus-omxh25-portable-backup-v1",
            "research_only": True, "trade_ready": False, "benchmark_identity_verified": False,
            "original_artifact_id": 13680073011,
            "original_artifact_sha256": "6849ebe332ce2be42e51cd9c8537b12e755e739bc4fc4a25ec5bccfcb70fc277",
            "files": {"original-capture.zip": "6849ebe332ce2be42e51cd9c8537b12e755e739bc4fc4a25ec5bccfcb70fc277",
                      "offline-recovery-receipt.json": "invalid"},
        }
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("original-capture.zip", original)
            z.writestr("offline-recovery-receipt.json", json.dumps(receipt or {}))
            z.writestr("manifest.json", json.dumps(manifest))
        return path

    def test_tampered_capture_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "PORTABLE_BACKUP_HASH_MISMATCH"):
                verify_portable_backup(self.make_backup(Path(d)))

    def test_trade_ready_promotion_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = self.make_backup(root)
            with zipfile.ZipFile(path) as z:
                manifest = json.loads(z.read("manifest.json"))
            manifest["trade_ready"] = True
            with self.assertRaisesRegex(ValueError, "PORTABLE_BACKUP_MANIFEST_INVALID"):
                verify_portable_backup(self.make_backup(root, manifest=manifest))

    def test_missing_source_member_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "backup.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("manifest.json", "{}")
            with self.assertRaisesRegex(ValueError, "PORTABLE_BACKUP_MEMBERS_INVALID"):
                verify_portable_backup(path)

    def test_no_overwriting_backup_with_recovery_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            backup = root / "backup.zip"
            backup.write_bytes(b"do not overwrite")
            with self.assertRaisesRegex(ValueError, "PORTABLE_RECOVERY_PATH_COLLISION"):
                recover_portable_backup(backup, backup, root / "derived.zip", root / "receipt.json")
            self.assertEqual(backup.read_bytes(), b"do not overwrite")


if __name__ == "__main__":
    unittest.main()
