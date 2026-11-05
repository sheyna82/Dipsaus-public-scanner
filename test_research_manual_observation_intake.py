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
        self.assertEqual(result["timing_classification"], "same_day_registration_requires_exchange_cutoff_proof")
        self.assertFalse(result["prospective_signal_proven"])
        self.assertFalse(result["independent_market_data_provenance"])
        self.assertFalse(result["trade_ready"])

    def test_late_registration_is_explicitly_nonprospective(self):
        with patch("research_manual_observation_intake.datetime") as dt:
            dt.now.return_value = datetime(2026, 11, 4, 16, tzinfo=timezone.utc)
            result = run_manual_intake(
                self.observation, self.source, self.candidates, self.archive,
                allowed_hosts=["example.org"])
        self.assertEqual(
            result["timing_classification"],
            "late_registration_not_prospective_for_signal_session")
        self.assertFalse(result["prospective_signal_proven"])

    def test_alpha_vantage_validated_before_registration(self):
        self.source.write_text(json.dumps({
            "Meta Data": {"2. Symbol": "AMD"},
            "Time Series (Daily)": {"2026-11-03": {
                "1. open": "100", "2. high": "103", "3. low": "99",
                "4. close": "102", "5. volume": "12345"}}}))
        observation = json.loads(self.observation.read_text())
        observation["source_observed_at_utc"] = "2026-11-03T22:00:00Z"
        self.observation.write_text(json.dumps(observation))
        with patch("research_manual_observation_intake.datetime") as dt:
            dt.now.return_value = datetime(2026, 11, 3, 23, tzinfo=timezone.utc)
            result = run_manual_intake(
                self.observation, self.source, self.candidates, self.archive,
                allowed_hosts=["example.org"], provider_format="alpha_vantage_daily")
        self.assertFalse(result["trade_ready"])
        self.assertTrue(self.archive.exists())
        from zipfile import ZipFile
        with ZipFile(self.archive) as z:
            candidate = json.loads(z.read("candidate.json"))
        self.assertEqual(candidate["provider_bar"]["close"], 102.0)
        self.assertFalse(candidate["bar_available_at_observation_time_verified"])
        self.assertFalse(candidate["prospective_signal_proven"])

    def test_rejects_same_day_daily_close_before_cutoff(self):
        self.source.write_text(json.dumps({
            "Meta Data": {"2. Symbol": "AMD"},
            "Time Series (Daily)": {"2026-11-03": {
                "1. open": "100", "2. high": "103", "3. low": "99",
                "4. close": "102", "5. volume": "12345"}}}))
        with self.assertRaisesRegex(ValueError, "daily_bar_claimed_before_conservative_close"):
            run_manual_intake(
                self.observation, self.source, self.candidates, self.archive,
                allowed_hosts=["example.org"], provider_format="alpha_vantage_daily")
        self.assertFalse(self.archive.exists())
        self.assertEqual(list(self.candidates.iterdir()), [])

    def test_alpha_vantage_invalid_bar_does_not_register(self):
        self.source.write_text(json.dumps({
            "Meta Data": {"2. Symbol": "AMD"},
            "Time Series (Daily)": {"2026-11-03": {
                "1. open": "100", "2. high": "90", "3. low": "99",
                "4. close": "102", "5. volume": "12345"}}}))
        with self.assertRaisesRegex(ValueError, "inconsistent_daily_bar"):
            run_manual_intake(
                self.observation, self.source, self.candidates, self.archive,
                allowed_hosts=["example.org"], provider_format="alpha_vantage_daily")
        self.assertFalse(self.archive.exists())
        self.assertEqual(list(self.candidates.iterdir()), [])

    def test_rejects_caller_supplied_provider_proof(self):
        observation = json.loads(self.observation.read_text())
        observation["prospective_signal_proven"] = True
        self.observation.write_text(json.dumps(observation))
        with self.assertRaisesRegex(ValueError, "caller_supplied_provider_metadata_forbidden"):
            run_manual_intake(
                self.observation, self.source, self.candidates, self.archive,
                allowed_hosts=["example.org"], provider_format="alpha_vantage_daily")
        self.assertEqual(list(self.candidates.iterdir()), [])

    def test_unknown_provider_format_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unsupported_provider_format"):
            run_manual_intake(
                self.observation, self.source, self.candidates, self.archive,
                allowed_hosts=["example.org"], provider_format="unrecognized")
        self.assertEqual(list(self.candidates.iterdir()), [])

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
