"""Integration test: unverified source-shaped observation -> immutable ledger -> ZIP.

The example.org URL is a test fixture, NOT a retrieved market observation.
"""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research_real_observation_registration_bridge import register_validated_observation
from research_prospective_archive import archive_ledger, verify_archive
from research_registration_archive_bridge import inspect_candidate_archive


class RealShapedObservationArchiveIntegrationTests(unittest.TestCase):
    def test_observation_registration_and_archive_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates, outcomes = root / "candidates", root / "outcomes"
            candidates.mkdir()
            outcomes.mkdir()
            observed = {
                "symbol": "AMD", "protocol_id": "fixture-only-v1",
                "signal_session": "2026-11-03",
                "source_name": "fixture-not-actual-market-data",
                "source_url": "https://example.org/fixture/AMD",
                "source_observed_at_utc": "2026-11-03T15:00:00Z",
                "independent_source_authentication": False,
                "independent_timestamp_proof": False,
                "future_outcome": None,
                "research_only": True, "trade_ready": False,
            }
            result = register_validated_observation(
                observed, candidates,
                clock=lambda: datetime(2026, 11, 3, 16, tzinfo=timezone.utc))
            self.assertEqual(result["status"], "created")
            self.assertEqual(result["temporal_integrity"]["status"],
                             "same_day_registration_requires_exchange_cutoff_proof")
            self.assertFalse(result["temporal_integrity"]["prospective_signal_proven"])
            archive_path = root / "research-only.zip"
            archive_ledger(candidates, outcomes, archive_path)
            self.assertTrue(verify_archive(archive_path)["valid"])
            summary = inspect_candidate_archive(archive_path)
            self.assertEqual(summary["candidate_count"], 1)
            self.assertEqual(summary["candidates"][0]["identity"],
                             result["candidate_identity_sha256"])
            self.assertEqual(summary["candidates"][0]["sha256"], result["sha256"])
            self.assertFalse(summary["external_provenance_authenticated"])
            saved = json.loads(Path(result["path"]).read_text())
            self.assertFalse(saved["trade_ready"])
            self.assertIsNone(saved["future_outcome"])


if __name__ == "__main__":
    unittest.main()
