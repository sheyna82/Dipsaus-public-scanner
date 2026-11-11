"""Research-only snapshot integrity tests; no external data or live signals."""
import copy
import unittest
from research.us_setup_snapshot_contract import freeze_snapshot, verify_snapshot


class FrozenSetupSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.bars = [{"timestamp": "2026-10-01T14:30:00+00:00", "low": 99, "close": 100}]
        self.labels = [{"confirmed_utc": "2026-10-01T14:30:00+00:00", "source": "external_review"}]
        self.provenance = {"annotator": "external_reviewer", "method": "manual_blind_review",
                           "labeled_at_utc": "2026-10-05T12:00:00+00:00",
                           "source_dataset": "fixture"}

    def freeze(self, **changes):
        args = {"symbol": "CSGP", "bars": self.bars, "reference_episodes": self.labels,
                "label_provenance": self.provenance, "split": "test"}
        args.update(changes)
        return freeze_snapshot(**args)

    def test_hash_stable_for_same_input(self):
        self.assertEqual(self.freeze()["sha256"], self.freeze()["sha256"])

    def test_mutation_is_detected(self):
        snap = self.freeze()
        snap["snapshot"]["bars"][0]["close"] = 101
        self.assertFalse(verify_snapshot(snap))

    def test_missing_label_provenance_rejected(self):
        with self.assertRaises(ValueError):
            self.freeze(label_provenance={})

    def test_undeclared_split_rejected(self):
        with self.assertRaises(ValueError):
            self.freeze(split="live")

    def test_hash_does_not_claim_label_independence(self):
        snap = self.freeze()
        self.assertTrue(verify_snapshot(snap))
        self.assertFalse(snap["independence_verified"])
        self.assertTrue(snap["research_only"])


if __name__ == "__main__":
    unittest.main()
