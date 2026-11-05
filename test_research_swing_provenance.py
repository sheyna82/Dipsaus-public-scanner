"""Synthetic tests for swing research provenance chronology."""
import unittest
from research_swing_provenance import verify_research_provenance


def valid():
    return {"ticker": "EXAMPLE", "source_id": "offline-fixture",
            "strategy_version": "swing-research-v1", "signal_id": "fixture-001",
            "score": 1.5,
            "score_source_available_at": "2026-11-02T14:00:00Z",
            "signal_created_at": "2026-11-02T14:01:00Z",
            "entry_at": "2026-11-02T14:05:00Z",
            "outcome_source_available_at": "2026-11-10T22:00:00Z"}


class ProvenanceTests(unittest.TestCase):
    def test_valid_timestamps_and_stable_hash(self):
        a = verify_research_provenance(valid())
        b = verify_research_provenance(dict(reversed(list(valid().items()))))
        self.assertEqual(a["record_sha256"], b["record_sha256"])
        self.assertFalse(a["provider_timestamps_independently_authenticated"])

    def test_future_score_source_rejected(self):
        x = valid()
        x["score_source_available_at"] = "2026-11-02T14:02:00Z"
        with self.assertRaisesRegex(ValueError, "future_information"):
            verify_research_provenance(x)

    def test_signal_created_after_entry_rejected(self):
        x = valid()
        x["signal_created_at"] = "2026-11-02T14:06:00Z"
        with self.assertRaisesRegex(ValueError, "future_information"):
            verify_research_provenance(x)

    def test_outcome_before_entry_rejected(self):
        x = valid()
        x["outcome_source_available_at"] = "2026-11-02T14:00:00Z"
        with self.assertRaisesRegex(ValueError, "future_information"):
            verify_research_provenance(x)

    def test_naive_timestamp_rejected(self):
        x = valid()
        x["entry_at"] = "2026-11-02T14:05:00"
        with self.assertRaisesRegex(ValueError, "timezone"):
            verify_research_provenance(x)

    def test_hash_changes_when_score_changes(self):
        a = valid()
        b = valid()
        b["score"] = 2.5
        self.assertNotEqual(verify_research_provenance(a)["record_sha256"],
                            verify_research_provenance(b)["record_sha256"])

    def test_invalid_score_rejected(self):
        x = valid()
        x["score"] = float("nan")
        with self.assertRaisesRegex(ValueError, "invalid_score"):
            verify_research_provenance(x)


if __name__ == "__main__":
    unittest.main()
