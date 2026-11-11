"""Synthetic multi-run registration-to-archive integration tests (research only)."""
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


def create_archive(path, candidate_path):
    raw = Path(candidate_path).read_bytes()
    member = "candidates/" + Path(candidate_path).name
    manifest = {"format_version": 1, "research_only": True,
                "trade_ready": False, "files": [
                    {"path": member, "bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest()}]}
    with ZipFile(path, "x") as archive:
        archive.writestr(member, raw)
        archive.writestr("manifest.json", json.dumps(manifest))


class MultiRunArchiveIntegrationTests(unittest.TestCase):
    def candidate(self, symbol):
        return {"symbol": symbol, "signal_session": "2026-11-02",
                "protocol_id": "v1", "future_outcome": None, "trade_ready": False}

    def register(self, directory, symbol, hour):
        directory.mkdir()
        return register_candidate_once(self.candidate(symbol), directory,
            clock=lambda: datetime(2026, 11, 3, hour, tzinfo=timezone.utc))

    def test_same_record_across_archives_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registered = self.register(root / "run1", "AMD", 15)
            a, b = root / "a.zip", root / "b.zip"
            create_archive(a, registered["path"])
            create_archive(b, registered["path"])
            summaries = [inspect_candidate_archive(p) for p in (a, b)]
            result = reconcile_verified_archive_summaries(summaries)
            self.assertEqual(result["candidate_count"], 1)
            self.assertFalse(result["all_historical_archives_discovered"])
            self.assertFalse(result["trade_ready"])

    def test_distinct_runs_preserve_distinct_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = self.register(root / "run1", "AMD", 15)
            b = self.register(root / "run2", "COHU", 16)
            archives = [root / "a.zip", root / "b.zip"]
            create_archive(archives[0], a["path"])
            create_archive(archives[1], b["path"])
            result = reconcile_verified_archive_summaries(
                [inspect_candidate_archive(p) for p in archives])
            self.assertEqual(result["candidate_count"], 2)

    def test_same_signal_re_registered_in_later_run_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = self.register(root / "run1", "AMD", 15)
            b = self.register(root / "run2", "AMD", 16)
            archives = [root / "a.zip", root / "b.zip"]
            create_archive(archives[0], a["path"])
            create_archive(archives[1], b["path"])
            with self.assertRaisesRegex(ValueError, "cross_archive_candidate_conflict"):
                reconcile_verified_archive_summaries(
                    [inspect_candidate_archive(p) for p in archives])


if __name__ == "__main__":
    unittest.main()
