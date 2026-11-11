import json
import socket
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from research_offline_observation_archive import archive_offline_observation
from research_source_evidence_archive import verify_source_evidence_archive


class OfflineObservationArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.candidates = self.root / "candidates"
        self.candidates.mkdir()
        self.archive = self.root / "evidence.zip"
        self.source = b'{"symbol":"AMD","sample":true}'
        self.clock = lambda: datetime(2026, 11, 3, 16, tzinfo=timezone.utc)
        self.observation = {
            "symbol": "AMD", "protocol_id": "offline-integration-test",
            "signal_session": "2026-11-03",
            "source_name": "user-supplied-unverified-bytes",
            "source_url": "https://example.org/market.json",
            "source_observed_at_utc": "2026-11-03T15:00:00Z",
            "independent_source_authentication": False,
            "independent_timestamp_proof": False,
            "research_only": True, "trade_ready": False,
            "future_outcome": None,
        }

    def intake(self, observation=None):
        return archive_offline_observation(
            observation or self.observation, self.source, self.candidates,
            self.archive, clock=self.clock, allowed_hosts={"example.org"})

    def test_complete_archive_without_network(self):
        with patch.object(socket, "getaddrinfo", side_effect=AssertionError("DNS used")):
            with patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
                result = self.intake()
        self.assertEqual(result["registration"]["status"], "created")
        self.assertEqual(result["archive_verification"]["status"],
                         "source_bytes_and_candidate_locally_verified")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["independent_timestamp_proof"])
        self.assertEqual(verify_source_evidence_archive(self.archive)["source_sha256"],
                         result["source_sha256"])
        candidate = json.loads(Path(result["registration"]["path"]).read_text())
        self.assertTrue(candidate["offline_supplied_bytes"])
        self.assertFalse(candidate["source_bytes_independently_authenticated"])

    def test_no_overwrite_of_existing_archive(self):
        self.archive.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            self.intake()
        self.assertEqual(self.archive.read_bytes(), b"existing")
        self.assertEqual(list(self.candidates.iterdir()), [])

    def test_future_observation_rejected(self):
        with self.assertRaisesRegex(ValueError, "future_observation"):
            self.intake({**self.observation,
                         "source_observed_at_utc": "2026-11-04T00:00:00Z"})
        self.assertFalse(self.archive.exists())

    def test_rejects_false_authentication_claim(self):
        with self.assertRaisesRegex(ValueError, "unsupported_source_authentication_claim"):
            self.intake({**self.observation, "independent_source_authentication": True})
        self.assertFalse(self.archive.exists())


if __name__ == "__main__":
    unittest.main()
