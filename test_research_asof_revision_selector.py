"""Regression tests for as-of historical revision selection."""

import unittest
from research_asof_revision_selector import select_asof_revision


def version(name, published, ingested):
    return {"revision_id": name, "published_at": published, "ingested_at": ingested}


EARLY = version("original", "2026-01-01T09:00:00+00:00", "2026-01-01T09:01:00+00:00")
LATER = version("revised", "2026-01-03T09:00:00+00:00", "2026-01-03T09:01:00+00:00")


class AsOfRevisionTests(unittest.TestCase):
    def test_original_before_revision(self):
        result = select_asof_revision([LATER, EARLY], decision_at="2026-01-02T10:00:00+00:00")
        self.assertEqual(result["revision_id"], "original")
        self.assertFalse(result["historical_snapshot_verified"])

    def test_revised_after_ingestion(self):
        result = select_asof_revision([EARLY, LATER], decision_at="2026-01-04T10:00:00+00:00")
        self.assertEqual(result["revision_id"], "revised")

    def test_not_yet_ingested(self):
        result = select_asof_revision([EARLY, LATER], decision_at="2026-01-03T09:00:30+00:00")
        self.assertEqual(result["revision_id"], "original")

    def test_no_available_version(self):
        result = select_asof_revision([LATER], decision_at="2026-01-02T10:00:00+00:00")
        self.assertFalse(result["accepted"])

    def test_duplicate_revision_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_or_duplicate_revision_id"):
            select_asof_revision([EARLY, EARLY], decision_at="2026-01-04T10:00:00+00:00")

    def test_ingestion_before_publication_rejected(self):
        bad = version("bad", "2026-01-03T10:00:00+00:00", "2026-01-03T09:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "ingestion_before_publication"):
            select_asof_revision([bad], decision_at="2026-01-04T10:00:00+00:00")

    def test_ambiguous_revision_order_rejected(self):
        other = {**EARLY, "revision_id": "same-time"}
        with self.assertRaisesRegex(ValueError, "ambiguous_revision_order"):
            select_asof_revision([EARLY, other], decision_at="2026-01-04T10:00:00+00:00")

    def test_publication_before_observation_rejected(self):
        bad = {**EARLY, "observed_at": "2026-01-02T09:00:00+00:00"}
        with self.assertRaisesRegex(ValueError, "publication_before_observation"):
            select_asof_revision([bad], decision_at="2026-01-04T10:00:00+00:00")

    def test_observation_before_publication_accepted(self):
        good = {**EARLY, "observed_at": "2026-01-01T08:00:00+00:00"}
        result = select_asof_revision([good], decision_at="2026-01-02T10:00:00+00:00")
        self.assertEqual(result["revision_id"], "original")


if __name__ == "__main__":
    unittest.main()
