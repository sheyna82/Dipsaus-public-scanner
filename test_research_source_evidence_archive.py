import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from research_source_bound_registration import register_observation_with_source_snapshot
from research_source_evidence_archive import archive_source_evidence, verify_source_evidence_archive


class SourceEvidenceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.candidates = self.root / "candidates"
        self.candidates.mkdir()
        self.source = b'{"fixture":true,"close":123.45}'
        observation = {
            "symbol": "AMD", "protocol_id": "fixture-v1", "signal_session": "2026-11-03",
            "source_name": "test-fixture", "source_url": "https://example.org/fixture",
            "source_observed_at_utc": "2026-11-03T15:00:00Z",
            "independent_source_authentication": False, "independent_timestamp_proof": False,
            "research_only": True, "trade_ready": False, "future_outcome": None,
        }
        self.record = register_observation_with_source_snapshot(
            observation, self.source, self.candidates,
            clock=lambda: datetime(2026, 11, 3, 16, tzinfo=timezone.utc))
        self.zip_path = self.root / "source-evidence.zip"

    def tearDown(self):
        self.tmp.cleanup()

    def test_source_bytes_and_candidate_are_archived_and_verified(self):
        result = archive_source_evidence(self.record["path"], self.source, self.zip_path)
        self.assertEqual(result["status"], "source_bytes_and_candidate_locally_verified")
        self.assertFalse(result["independent_source_authentication"])
        with ZipFile(self.zip_path) as z:
            self.assertEqual(z.read("source.bin"), self.source)
            self.assertFalse(json.loads(z.read("candidate.json"))["trade_ready"])

    def test_wrong_source_rejected_before_archive(self):
        with self.assertRaisesRegex(ValueError, "source_candidate_binding_mismatch"):
            archive_source_evidence(self.record["path"], b"modified", self.zip_path)
        self.assertFalse(self.zip_path.exists())

    def test_duplicate_archive_not_overwritten(self):
        archive_source_evidence(self.record["path"], self.source, self.zip_path)
        with self.assertRaises(FileExistsError):
            archive_source_evidence(self.record["path"], self.source, self.zip_path)

    def test_tampered_archive_detected(self):
        archive_source_evidence(self.record["path"], self.source, self.zip_path)
        with ZipFile(self.zip_path, "a") as z:
            z.writestr("unexpected.bin", b"x")
        with self.assertRaisesRegex(ValueError, "invalid_source_archive_members"):
            verify_source_evidence_archive(self.zip_path)


if __name__ == "__main__":
    unittest.main()
