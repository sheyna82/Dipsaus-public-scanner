"""Structural walk-forward leakage regression tests."""

import unittest
from research_walk_forward_split_gate import validate_walk_forward_split


def row(event, available):
    return {"event_at": event, "label_available_at": available}


T0 = "2026-01-01T09:00:00+00:00"
T1 = "2026-01-02T09:00:00+00:00"
T2 = "2026-01-03T09:00:00+00:00"
T3 = "2026-01-04T09:00:00+00:00"


class WalkForwardSplitTests(unittest.TestCase):
    def test_valid_chronological_split(self):
        result = validate_walk_forward_split([row(T0, T1)], [row(T2, T3)])
        self.assertTrue(result["accepted"])
        self.assertFalse(result["independent_source_verified"])
        self.assertFalse(result["trade_ready"])

    def test_future_training_label_rejected(self):
        with self.assertRaisesRegex(ValueError, "training_labels_not_available_before_holdout"):
            validate_walk_forward_split([row(T0, T3)], [row(T2, T3)])

    def test_embargo_enforced(self):
        with self.assertRaisesRegex(ValueError, "training_labels_not_available_before_holdout"):
            validate_walk_forward_split([row(T0, T1)], [row(T2, T3)], embargo_seconds=90000)

    def test_overlapping_events_rejected(self):
        with self.assertRaisesRegex(ValueError, "train_holdout_overlap"):
            validate_walk_forward_split([row(T0, T1)], [row(T0, T1)])

    def test_duplicate_training_event_rejected(self):
        with self.assertRaisesRegex(ValueError, "unordered_or_duplicate_events"):
            validate_walk_forward_split([row(T0, T1), row(T0, T1)], [row(T2, T3)])

    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone_required"):
            validate_walk_forward_split([row("2026-01-01T09:00:00", T1)], [row(T2, T3)])

    def test_label_before_event_rejected(self):
        with self.assertRaisesRegex(ValueError, "label_before_event"):
            validate_walk_forward_split([row(T1, T0)], [row(T2, T3)])


    def test_feature_published_after_event_rejected(self):
        late_feature = {**row(T0, T1), "feature_available_at": T1}
        with self.assertRaisesRegex(ValueError, "feature_not_available_at_event"):
            validate_walk_forward_split([late_feature], [row(T2, T3)])

    def test_feature_available_at_event_accepted(self):
        timely_feature = {**row(T0, T1), "feature_available_at": T0}
        result = validate_walk_forward_split([timely_feature], [row(T2, T3)])
        self.assertTrue(result["accepted"])
        self.assertFalse(result["independent_source_verified"])

    def test_empty_split_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty_split"):
            validate_walk_forward_split([], [row(T2, T3)])

    def test_invalid_embargo_rejected(self):
        for value in (-1, True, 1.5):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid_embargo"):
                    validate_walk_forward_split([row(T0, T1)], [row(T2, T3)], embargo_seconds=value)


if __name__ == "__main__":
    unittest.main()
