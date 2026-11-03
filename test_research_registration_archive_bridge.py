import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from research_immutable_candidate_registration import register_candidate_once
from research_registration_archive_bridge import (
    inspect_candidate_archive, reconcile_verified_archive_summaries)


def make_archive(path, candidate_bytes):
    member = "candidates/candidate.json"
    manifest = {"format_version": 1, "trade_ready": False, "files": [{
        "path": member, "bytes": len(candidate_bytes),
        "sha256": hashlib.sha256(candidate_bytes).hexdigest()}]}
    with ZipFile(path, "w") as z:
        z.writestr(member, candidate_bytes)
        z.writestr("manifest.json", json.dumps(manifest))


class ArchiveBridgeTests(unittest.TestCase):
    def test_valid_archive_and_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = {"symbol": "AMD", "signal_session": "2026-11-02",
                         "protocol_id": "v1", "future_outcome": None, "trade_ready": False}
            registered = register_candidate_once(candidate, tmp,
                clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            archive = Path(tmp) / "archive.zip"
            make_archive(archive, Path(registered["path"]).read_bytes())
            summary = inspect_candidate_archive(archive)
            self.assertEqual(summary["candidate_count"], 1)
            combined = reconcile_verified_archive_summaries([summary, summary])
            self.assertEqual(combined["candidate_count"], 1)
            self.assertFalse(combined["external_provenance_authenticated"])

    def test_checksum_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "archive.zip"
            make_archive(archive, b'{"trade_ready":false}')
            with ZipFile(archive, "a") as z:
                z.writestr("candidates/candidate.json", b"tampered")
            with self.assertRaisesRegex(ValueError, "invalid_archive_members"):
                inspect_candidate_archive(archive)

    def test_conflicting_summaries_rejected(self):
        first = {"status": "archive_manifest_verified",
                 "candidates": [{"identity": "same", "sha256": "a"}]}
        second = {"status": "archive_manifest_verified",
                  "candidates": [{"identity": "same", "sha256": "b"}]}
        with self.assertRaisesRegex(ValueError, "cross_archive_candidate_conflict"):
            reconcile_verified_archive_summaries([first, second])


if __name__ == "__main__":
    unittest.main()
