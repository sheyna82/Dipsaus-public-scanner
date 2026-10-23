"""Synthetic point-in-time audit regression tests."""

import unittest
from research_point_in_time_availability_gate import assess_point_in_time_record

DECISION = "2026-01-05T10:00:00+00:00"
RECORD = {
    "observed_at": "2026-01-04T09:00:00+00:00",
    "published_at": "2026-01-04T10:00:00+00:00",
    "ingested_at": "2026-01-04T13:00:00+00:00",
    "revision_asof": "2026-01-04T12:00:00+00:00",
}


class PointInTimeTests(unittest.TestCase):
    def check(self, changes=None):
        return assess_point_in_time_record({**RECORD, **(changes or {})}, decision_at=DECISION)

    def test_valid_metadata(self):
        result = self.check()
        self.assertTrue(result["accepted"])
        self.assertFalse(result["historical_snapshot_verified"])

    def test_future_publication_rejected(self):
        result = self.check({"published_at": "2026-01-06T10:00:00+00:00",
                             "ingested_at": "2026-01-06T11:00:00+00:00"})
        self.assertIn("future_published_at", result["reasons"])

    def test_future_ingestion_rejected(self):
        self.assertIn("future_ingested_at", self.check(
            {"ingested_at": "2026-01-06T11:00:00+00:00"})["reasons"])

    def test_future_revision_rejected(self):
        self.assertIn("future_revision_asof", self.check(
            {"revision_asof": "2026-01-06T11:00:00+00:00"})["reasons"])

    def test_missing_metadata_rejected(self):
        for key in RECORD:
            with self.subTest(key=key):
                self.assertIn("invalid_" + key, self.check({key: None})["reasons"])

    def test_naive_metadata_rejected(self):
        self.assertIn("invalid_published_at", self.check(
            {"published_at": "2026-01-04T10:00:00"})["reasons"])

    def test_publication_order_rejected(self):
        self.assertIn("publication_before_observation", self.check(
            {"published_at": "2026-01-03T10:00:00+00:00"})["reasons"])

    def test_ingestion_order_rejected(self):
        self.assertIn("ingestion_before_publication", self.check(
            {"ingested_at": "2026-01-04T09:30:00+00:00"})["reasons"])

    def test_future_observation_rejected(self):
        result = self.check({
            "observed_at": "2026-01-06T09:00:00+00:00",
            "published_at": "2026-01-06T10:00:00+00:00",
            "ingested_at": "2026-01-06T13:00:00+00:00",
            "revision_asof": "2026-01-06T12:00:00+00:00",
        })
        self.assertIn("future_observed_at", result["reasons"])

    def test_revision_before_publication_rejected(self):
        result = self.check({"revision_asof": "2026-01-04T09:30:00+00:00"})
        self.assertIn("revision_before_publication", result["reasons"])

    def test_timezone_equivalence(self):
        result = self.check({
            "observed_at": "2026-01-04T10:00:00+01:00",
            "published_at": "2026-01-04T11:00:00+01:00",
            "ingested_at": "2026-01-04T14:00:00+01:00",
            "revision_asof": "2026-01-04T13:00:00+01:00",
        })
        self.assertTrue(result["accepted"])

    def test_revision_not_yet_ingested_rejected(self):
        result = self.check({"revision_asof": "2026-01-04T14:00:00+00:00"})
        self.assertIn("revision_not_yet_ingested", result["reasons"])


if __name__ == "__main__":
    unittest.main()
