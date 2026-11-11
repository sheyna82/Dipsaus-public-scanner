import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research_source_bound_registration import register_observation_with_source_snapshot
from research_prospective_archive import archive_ledger
from research_registration_archive_bridge import inspect_candidate_archive
from zipfile import ZipFile


class SourceBoundRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.candidates = self.root / "candidates"
        self.outcomes = self.root / "outcomes"
        self.candidates.mkdir()
        self.outcomes.mkdir()
        self.source = b'{"fixture":true,"close":123.45}'
        self.observation = {
            "symbol": "AMD", "protocol_id": "source-fixture-v1",
            "signal_session": "2026-11-03",
            "source_name": "fixture-not-market-data",
            "source_url": "https://example.org/fixture",
            "source_observed_at_utc": "2026-11-03T15:00:00Z",
            "independent_source_authentication": False,
            "independent_timestamp_proof": False,
            "research_only": True, "trade_ready": False, "future_outcome": None,
        }
        self.clock = lambda: datetime(2026, 11, 3, 16, tzinfo=timezone.utc)

    def tearDown(self):
        self.tmp.cleanup()

    def register(self):
        return register_observation_with_source_snapshot(
            self.observation, self.source, self.candidates, clock=self.clock)

    def test_snapshot_digest_persists_into_immutable_candidate_and_archive(self):
        result = self.register()
        digest = hashlib.sha256(self.source).hexdigest()
        self.assertEqual(result["source_snapshot_sha256"], digest)
        self.assertFalse(result["source_bytes_archived"])
        stored = json.loads(Path(result["path"]).read_text())
        self.assertEqual(stored["source_snapshot_sha256"], digest)
        self.assertEqual(stored["source_snapshot_bytes"], len(self.source))
        zip_path = self.root / "archive.zip"
        archive_ledger(self.candidates, self.outcomes, zip_path)
        summary = inspect_candidate_archive(zip_path)
        self.assertEqual(summary["candidate_count"], 1)
        with ZipFile(zip_path) as archive:
            self.assertEqual(json.loads(archive.read(
                "candidates/" + Path(result["path"]).name))["source_snapshot_sha256"], digest)

    def test_modified_source_cannot_overwrite_existing_candidate(self):
        result = self.register()
        original = Path(result["path"]).read_bytes()
        self.source = b'{"fixture":true,"close":999.99}'
        with self.assertRaisesRegex(ValueError, "candidate_already_registered_with_different_payload"):
            self.register()
        self.assertEqual(Path(result["path"]).read_bytes(), original)

    def test_empty_source_does_not_register(self):
        self.source = b""
        with self.assertRaisesRegex(ValueError, "missing_source_bytes"):
            self.register()
        self.assertEqual(list(self.candidates.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
