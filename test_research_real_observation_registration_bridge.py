import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research_real_observation_registration_bridge import register_validated_observation


class RealObservationRegistrationBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.clock = lambda: datetime(2026, 11, 3, 16, tzinfo=timezone.utc)
        self.record = {
            "symbol": "AMD", "protocol_id": "research-v1",
            "signal_session": "2026-11-02", "source_name": "unverified-test-source",
            "source_url": "https://example.org/market/AMD",
            "source_observed_at_utc": "2026-11-03T15:00:00Z",
            "independent_source_authentication": False,
            "independent_timestamp_proof": False,
            "future_outcome": None, "research_only": True, "trade_ready": False,
        }

    def tearDown(self):
        self.tmp.cleanup()

    def register(self):
        return register_validated_observation(self.record, self.root, clock=self.clock)

    def test_valid_observation_registered_without_evidence_promotion(self):
        result = self.register()
        self.assertEqual(result["status"], "created")
        self.assertFalse(result["independent_market_data_provenance"])
        payload = json.loads(Path(result["path"]).read_text())
        self.assertEqual(payload["source_url"], self.record["source_url"])
        self.assertFalse(payload["registration_clock_proof_independent"])
        self.assertFalse(payload["trade_ready"])

    def test_re_registration_does_not_overwrite_original(self):
        result = self.register()
        original = Path(result["path"]).read_bytes()
        with self.assertRaisesRegex(ValueError, "candidate_already_registered_with_different_payload"):
            self.register()
        self.assertEqual(Path(result["path"]).read_bytes(), original)

    def test_future_source_rejected_before_file_creation(self):
        self.record["source_observed_at_utc"] = "2026-11-04T15:00:00Z"
        with self.assertRaisesRegex(ValueError, "future_observation"):
            self.register()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_unsupported_authentication_claim_rejected(self):
        self.record["independent_source_authentication"] = True
        with self.assertRaisesRegex(ValueError, "unsupported_source_authentication_claim"):
            self.register()
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
