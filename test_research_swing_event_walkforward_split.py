"""Tests for chronological event-study split and label embargo."""
import unittest
from research_swing_event_walkforward_split import partition_event_windows

def row(name, available, end):
    return {"symbol": "ABC", "event_id": name,
            "available_at_utc": available + "T12:00:00Z",
            "outcome_end_at_utc": end + "T12:00:00Z"}

V = "2020-01-01T00:00:00Z"
T = "2022-01-01T00:00:00Z"

class WalkforwardSplitTests(unittest.TestCase):
    def test_train_validation_and_test(self):
        records = [row("a", "2018-01-01", "2018-02-01"),
                   row("b", "2020-06-01", "2020-06-30"),
                   row("c", "2022-02-01", "2022-02-20")]
        result = partition_event_windows(records, validation_start=V, test_start=T)
        self.assertEqual(result["counts"], {"train": 1, "validation": 1,
                                             "test": 1, "excluded": 0})
    def test_training_label_leakage_excluded(self):
        result = partition_event_windows(
            [row("a", "2019-12-01", "2019-12-25")],
            validation_start=V, test_start=T)
        self.assertEqual(result["counts"]["excluded"], 1)
    def test_validation_label_leakage_excluded(self):
        result = partition_event_windows(
            [row("a", "2021-12-01", "2021-12-25")],
            validation_start=V, test_start=T)
        self.assertEqual(result["counts"]["excluded"], 1)
    def test_invalid_boundary_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_split_boundaries"):
            partition_event_windows([], validation_start=T, test_start=V)
    def test_duplicate_rejected(self):
        a = row("a", "2018-01-01", "2018-02-01")
        with self.assertRaisesRegex(ValueError, "duplicate_event"):
            partition_event_windows([a, a], validation_start=V, test_start=T)
    def test_negative_embargo_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_embargo"):
            partition_event_windows([], validation_start=V, test_start=T, embargo_days=-1)

if __name__ == "__main__":
    unittest.main()
