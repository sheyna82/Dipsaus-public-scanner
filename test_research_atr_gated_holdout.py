"""Regression tests for structural gating of ATR holdout scoring."""
import unittest

from research_atr_gated_holdout import evaluate_gated_atr_holdout


def row(day, severe, atr):
    return {
        "event_at": f"2026-01-{day:02d}T09:00:00+00:00",
        "observed_at": f"2026-01-{day:02d}T08:00:00+00:00",
        "published_at": f"2026-01-{day:02d}T08:10:00+00:00",
        "ingested_at": f"2026-01-{day:02d}T08:20:00+00:00",
        "revision_asof": f"2026-01-{day:02d}T08:10:00+00:00",
        "label_available_at": f"2026-01-{day:02d}T18:00:00+00:00",
        "structure_above_20d_mean": True,
        "market_20d_positive": True,
        "atr_expanding": atr,
        "severe": severe,
    }


EVALUATION_AT = "2026-01-10T12:00:00+00:00"


class GatedATRHoldoutTests(unittest.TestCase):
    def test_valid_split_remains_descriptive(self):
        result = evaluate_gated_atr_holdout(
            [row(1, False, False), row(2, True, True)],
            [row(4, False, False)], evaluation_at=EVALUATION_AT)
        self.assertTrue(result["structural_split_accepted"])
        self.assertEqual(result["events"], 1)
        self.assertFalse(result["independent_source_verified"])
        self.assertFalse(result["independent_holdout_verified"])
        self.assertFalse(result["trade_ready"])
        self.assertTrue(result["descriptive_only"])

    def test_overlapping_split_rejected_before_scoring(self):
        with self.assertRaisesRegex(ValueError, "train_holdout_overlap"):
            evaluate_gated_atr_holdout(
                [row(1, False, False), row(4, True, True)],
                [row(3, False, False)], evaluation_at=EVALUATION_AT)

    def test_unavailable_training_label_rejected(self):
        delayed = {**row(2, True, True),
                   "label_available_at": "2026-01-06T18:00:00+00:00"}
        with self.assertRaisesRegex(
                ValueError, "training_labels_not_available_before_holdout"):
            evaluate_gated_atr_holdout(
                [row(1, False, False), delayed],
                [row(4, False, False)])

    def test_future_feature_publication_rejected(self):
        bad = {**row(4, False, False),
               "published_at": "2026-01-04T10:00:00+00:00",
               "ingested_at": "2026-01-04T10:10:00+00:00",
               "revision_asof": "2026-01-04T10:00:00+00:00"}
        with self.assertRaisesRegex(ValueError, "point_in_time_rejected"):
            evaluate_gated_atr_holdout([row(1, False, False)], [bad], evaluation_at=EVALUATION_AT)

    def test_holdout_label_unavailable_at_evaluation_rejected(self):
        with self.assertRaisesRegex(ValueError, "holdout_labels_not_yet_available"):
            evaluate_gated_atr_holdout(
                [row(1, False, False)], [row(4, False, False)],
                evaluation_at="2026-01-04T12:00:00+00:00")

    def test_embargo_enforced(self):
        with self.assertRaisesRegex(
                ValueError, "training_labels_not_available_before_holdout"):
            evaluate_gated_atr_holdout(
                [row(1, False, False)], [row(2, False, False)],
                embargo_seconds=86400, evaluation_at=EVALUATION_AT)


if __name__ == "__main__":
    unittest.main()
