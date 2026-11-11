"""Integration checks across revision selection, point-in-time and holdout gates."""

import unittest

from research_asof_revision_selector import select_asof_revision
from research_point_in_time_availability_gate import assess_point_in_time_record
from research_walk_forward_split_gate import validate_walk_forward_split

DECISION = "2026-01-05T12:00:00+00:00"
ORIGINAL = {
    "revision_id": "original",
    "observed_at": "2026-01-01T09:00:00+00:00",
    "published_at": "2026-01-01T10:00:00+00:00",
    "ingested_at": "2026-01-01T11:00:00+00:00",
    "revision_asof": "2026-01-01T10:00:00+00:00",
}
REVISION = {
    **ORIGINAL,
    "revision_id": "revised",
    "published_at": "2026-01-06T10:00:00+00:00",
    "ingested_at": "2026-01-06T11:00:00+00:00",
    "revision_asof": "2026-01-06T10:00:00+00:00",
}


class IntegratedHistoricalGatesTests(unittest.TestCase):
    def test_select_then_validate_original(self):
        selected = select_asof_revision([REVISION, ORIGINAL], decision_at=DECISION)
        self.assertEqual(selected["revision_id"], "original")
        record = next(v for v in (ORIGINAL, REVISION) if v["revision_id"] == selected["revision_id"])
        audit = assess_point_in_time_record(record, decision_at=DECISION)
        self.assertTrue(audit["accepted"])
        self.assertFalse(audit["historical_snapshot_verified"])

    def test_future_revision_is_excluded(self):
        selected = select_asof_revision([ORIGINAL, REVISION], decision_at=DECISION)
        self.assertEqual(selected["revision_id"], "original")
        audit = assess_point_in_time_record(REVISION, decision_at=DECISION)
        self.assertFalse(audit["accepted"])
        self.assertIn("future_revision_asof", audit["reasons"])

    def test_holdout_rejects_unavailable_training_label(self):
        train = [{"event_at": "2026-01-01T09:00:00+00:00",
                  "label_available_at": "2026-01-07T09:00:00+00:00"}]
        holdout = [{"event_at": DECISION,
                    "label_available_at": "2026-01-06T12:00:00+00:00"}]
        with self.assertRaisesRegex(ValueError, "training_labels_not_available_before_holdout"):
            validate_walk_forward_split(train, holdout)

    def test_independent_provenance_not_claimed(self):
        result = select_asof_revision([ORIGINAL], decision_at=DECISION)
        self.assertFalse(result["historical_snapshot_verified"])
        self.assertFalse(result["trade_ready"])


if __name__ == "__main__":
    unittest.main()
