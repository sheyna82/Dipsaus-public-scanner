import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from research_manual_observation_intake import run_manual_intake


class ManualObservationIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.observation = self.root / "observation.json"
        self.source = self.root / "source.bin"
        self.candidates = self.root / "candidates"
        self.candidates.mkdir()
        self.archive = self.root / "evidence.zip"
        self.source.write_bytes(b'{"market":"sample"}')
        self.observation.write_text(json.dumps({
            "symbol": "AMD", "protocol_id": "manual-source-test",
            "signal_session": "2026-11-03",
            "source_name": "unverified-local-snapshot",
            "source_url": "https://example.org/data",
            "source_observed_at_utc": "2026-11-03T15:00:00Z",
            "independent_source_authentication": False,
            "independent_timestamp_proof": False,
            "research_only": True, "trade_ready": False,
            "future_outcome": None,
        }))

    def test_manual_intake_creates_verified_local_archive(self):
        with patch("research_manual_observation_intake.datetime") as dt:
            dt.now.return_value = datetime(2026, 11, 3, 16, tzinfo=timezone.utc)
            result = run_manual_intake(
                self.observation, self.source, self.candidates, self.archive,
                allowed_hosts=["example.org"])
        self.assertEqual(result["status"], "offline_observation_archived_unverified")
        self.assertTrue(self.archive.exists())
        self.assertFalse(result["independent_market_data_provenance"])
        self.assertFalse(result["trade_ready"])

    def test_rejects_missing_source_file(self):
        self.source.unlink()
        with self.assertRaisesRegex(ValueError, "invalid_source_file"):
            run_manual_intake(self.observation, self.source, self.candidates,
                              self.archive, allowed_hosts=["example.org"])

    def test_rejects_non_object_observation(self):
        self.observation.write_text("[]")
        with self.assertRaisesRegex(ValueError, "observation_must_be_object"):
            run_manual_intake(self.observation, self.source, self.candidates,
                              self.archive, allowed_hosts=["example.org"])


if __name__ == "__main__":
    unittest.main()
