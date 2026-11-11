"""Synthetic walk-forward boundary and embargo tests."""
import unittest
from research_swing_walk_forward_split import purged_walk_forward_split


def sample(id_, entry, outcome):
    return {"sample_id": id_, "entry_date": entry, "outcome_date": outcome}


class WalkForwardSplitTests(unittest.TestCase):
    def test_purge_boundary_crossing_and_future(self):
        result = purged_walk_forward_split([
            sample("train", "2026-10-01", "2026-10-05"),
            sample("cross", "2026-10-08", "2026-10-13"),
            sample("test", "2026-10-12", "2026-10-16"),
            sample("late", "2026-10-16", "2026-10-23"),
            sample("future", "2026-10-21", "2026-10-24"),
        ], test_start="2026-10-12", test_end="2026-10-20")
        self.assertEqual(result["training_sample_ids"], ["train"])
        self.assertEqual(result["test_sample_ids"], ["test"])
        self.assertEqual(len(result["excluded_samples"]), 3)

    def test_embargo_excludes_recent_training_outcome(self):
        result = purged_walk_forward_split([
            sample("near", "2026-10-01", "2026-10-10"),
            sample("old", "2026-09-01", "2026-09-30"),
        ], test_start="2026-10-12", test_end="2026-10-20",
            embargo_calendar_days=3)
        self.assertEqual(result["training_sample_ids"], ["old"])
        self.assertEqual(result["excluded_samples"][0]["sample_id"], "near")

    def test_duplicate_id_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_or_invalid"):
            purged_walk_forward_split([
                sample("x", "2026-09-01", "2026-09-10"),
                sample("x", "2026-10-12", "2026-10-15"),
            ], test_start="2026-10-12", test_end="2026-10-20")

    def test_incomplete_test_outcome_excluded(self):
        result = purged_walk_forward_split([
            sample("x", "2026-10-19", "2026-10-22"),
        ], test_start="2026-10-12", test_end="2026-10-20")
        self.assertEqual(result["test_sample_ids"], [])
        self.assertEqual(result["excluded_samples"][0]["reason"],
                         "test_outcome_after_window")

    def test_invalid_embargo_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_embargo"):
            purged_walk_forward_split([], test_start="2026-10-12",
                                      test_end="2026-10-20",
                                      embargo_calendar_days=-1)

    def test_outcome_before_entry_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_outcome_window"):
            purged_walk_forward_split([
                sample("x", "2026-10-12", "2026-10-12"),
            ], test_start="2026-10-12", test_end="2026-10-20")


if __name__ == "__main__":
    unittest.main()
