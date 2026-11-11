import unittest
from research_swing_event_dataset_audit import audit_event_record, audit_event_dataset

BASE = {
    "symbol": "AMD", "event_id": "fy26q3", "kind": "earnings_release",
    "source": "issuer", "published_at": "2026-11-03T21:00:00Z",
    "first_observed_at": "2026-11-03T21:05:00+00:00",
    "release_timestamp_verified": True,
}

class EventDatasetAuditTests(unittest.TestCase):
    def test_observation_delay_is_respected(self):
        r = audit_event_record(BASE)
        self.assertEqual(r["available_at_utc"], "2026-11-03T21:05:00+00:00")
        self.assertTrue(r["research_eligible"])
        self.assertFalse(r["trade_ready"])

    def test_reject_naive_timezone(self):
        with self.assertRaisesRegex(ValueError, "timezone_required"):
            audit_event_record({**BASE, "published_at": "2026-11-03T21:00:00"})

    def test_reject_observed_before_published(self):
        with self.assertRaisesRegex(ValueError, "observed_before_publication"):
            audit_event_record({**BASE, "first_observed_at": "2026-11-03T20:00:00Z"})

    def test_unverified_release_excluded(self):
        r = audit_event_record({**BASE, "release_timestamp_verified": False})
        self.assertFalse(r["research_eligible"])

    def test_duplicate_flagged_not_silently_removed(self):
        r = audit_event_dataset([BASE, dict(BASE)])
        self.assertEqual([x["duplicate"] for x in r], [False, True])

if __name__ == "__main__":
    unittest.main()
