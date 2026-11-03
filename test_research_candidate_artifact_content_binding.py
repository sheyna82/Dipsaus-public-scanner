"""Content binding regression tests."""
import hashlib
import json
import unittest

from research_candidate_artifact_content_binding import bind_candidate_to_archive


class CandidateContentBindingTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {
            "candidate_identity_sha256": "a" * 64,
            "protocol_id": "research", "symbol": "TEST", "signal_session": "2026-11-02",
            "registered_at_utc": "2026-11-03T15:00:00+00:00",
            "research_only": True, "trade_ready": False, "future_outcome": None,
        }
        self.digest = hashlib.sha256(
            (json.dumps(self.candidate, sort_keys=True, separators=(",", ":")) + "\n").encode()
        ).hexdigest()
        self.archive = {"status": "archive_manifest_verified", "candidates": [
            {"identity": "a" * 64, "sha256": self.digest}
        ]}
        self.receipt = {
            "status": "receipt_metadata_consistent",
            "candidate_identity_sha256": "a" * 64,
            "github_run_id": 123, "artifact_id": 456,
        }

    def bind(self):
        return bind_candidate_to_archive(self.candidate, self.archive, self.receipt)

    def test_matching_content_bound_but_not_trade_ready(self):
        result = self.bind()
        self.assertTrue(result["candidate_in_artifact_verified"])
        self.assertFalse(result["github_artifact_download_digest_verified"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["independent_market_data_provenance"])

    def test_different_payload_rejected(self):
        self.candidate["symbol"] = "OTHER"
        with self.assertRaisesRegex(ValueError, "candidate_not_uniquely_bound_to_archive"):
            self.bind()

    def test_different_manifest_hash_rejected(self):
        self.archive["candidates"][0]["sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "candidate_not_uniquely_bound_to_archive"):
            self.bind()

    def test_duplicate_candidate_entries_rejected(self):
        self.archive["candidates"].append(dict(self.archive["candidates"][0]))
        with self.assertRaisesRegex(ValueError, "candidate_not_uniquely_bound_to_archive"):
            self.bind()

    def test_wrong_receipt_identity_rejected(self):
        self.receipt["candidate_identity_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "receipt_candidate_mismatch"):
            self.bind()

    def test_unverified_archive_rejected(self):
        self.archive["status"] = "unchecked"
        with self.assertRaisesRegex(ValueError, "archive_not_verified"):
            self.bind()

    def test_unverified_receipt_rejected(self):
        self.receipt["status"] = "unchecked"
        with self.assertRaisesRegex(ValueError, "receipt_not_verified"):
            self.bind()

    def test_trade_ready_candidate_rejected(self):
        self.candidate["trade_ready"] = True
        with self.assertRaisesRegex(ValueError, "unsafe_candidate"):
            self.bind()


if __name__ == "__main__":
    unittest.main()
