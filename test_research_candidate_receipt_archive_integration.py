"""Offline integration of immutable registration, archive and receipt checks.

The GitHub receipt here is deliberately simulated; no claim of external proof.
"""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research_immutable_candidate_registration import register_candidate_once
from research_prospective_archive import archive_ledger
from research_registration_archive_bridge import inspect_candidate_archive
from research_registration_receipt_gate import audit_registration_receipt
from research_candidate_artifact_content_binding import bind_candidate_to_archive


class CandidateReceiptArchiveIntegrationTests(unittest.TestCase):
    def test_full_local_archive_receipt_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates, outcomes = root / "candidates", root / "outcomes"
            candidates.mkdir()
            outcomes.mkdir()
            registered = register_candidate_once({
                "symbol": "AMD", "signal_session": "2026-11-02",
                "protocol_id": "research-v1", "trade_ready": False,
                "future_outcome": None,
            }, candidates, clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            import json
            candidate = json.loads(Path(registered["path"]).read_text())
            path = root / "archive.zip"
            archive_ledger(candidates, outcomes, path)
            archive_summary = inspect_candidate_archive(path)
            artifact = {
                "id": 456, "expired": False, "created_at": "2026-11-03T15:01:00Z",
                "digest": "sha256:" + "b" * 64,
                "workflow_run": {"id": 123, "head_sha": "c" * 40},
            }
            receipt = audit_registration_receipt(
                candidate, artifact, expected_run_id=123, expected_head_sha="c" * 40)
            result = bind_candidate_to_archive(candidate, archive_summary, receipt)
            self.assertEqual(result["status"], "candidate_archive_content_bound")
            self.assertTrue(result["candidate_in_artifact_verified"])
            self.assertFalse(result["github_artifact_download_digest_verified"])
            self.assertFalse(result["independent_pre_signal_timestamp_proof"])
            self.assertFalse(result["trade_ready"])

    def test_archive_replacement_cannot_bind_original_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates, outcomes = root / "candidates", root / "outcomes"
            candidates.mkdir()
            outcomes.mkdir()
            registered = register_candidate_once({
                "symbol": "AMD", "signal_session": "2026-11-02",
                "protocol_id": "research-v1", "trade_ready": False,
                "future_outcome": None,
            }, candidates, clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            import json
            original = json.loads(Path(registered["path"]).read_text())
            altered = dict(original)
            altered["symbol"] = "COHU"
            Path(registered["path"]).write_text(
                json.dumps(altered, sort_keys=True, separators=(",", ":")) + "\n")
            path = root / "archive.zip"
            archive_ledger(candidates, outcomes, path)
            with self.assertRaisesRegex(ValueError, "candidate_identity_digest_mismatch"):
                inspect_candidate_archive(path)


if __name__ == "__main__":
    unittest.main()
