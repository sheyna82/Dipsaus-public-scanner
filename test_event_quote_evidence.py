"""Offline regression tests for event quote evidence validation."""
import unittest
from datetime import datetime, timezone, timedelta
from event_quote_evidence import validated_event_quote


class QuoteEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc)
        self.observed = "2026-11-02T14:59:00+00:00"

    def test_valid_evidence(self):
        result = validated_event_quote(100.5, self.observed, "verified-feed", self.now)
        self.assertEqual(result["price"], 100.5)
        self.assertEqual(result["age_seconds"], 60)
        self.assertEqual(result["source"], "verified-feed")

    def test_fail_closed(self):
        cases = [
            (0, self.observed, "feed", self.now),
            (float("nan"), self.observed, "feed", self.now),
            (True, self.observed, "feed", self.now),
            (100, self.observed, "", self.now),
            (100, "2026-11-02T14:59:00", "feed", self.now),
            (100, "2026-11-02T14:55:00+00:00", "feed", self.now),
            (100, "2026-11-02T15:01:00+00:00", "feed", self.now),
            (100, "not-a-date", "feed", self.now),
            (100, self.observed, "feed", datetime(2026, 11, 2, 15)),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertIsNone(validated_event_quote(*args))

    def test_custom_age_limit(self):
        self.assertIsNotNone(validated_event_quote(
            100, self.observed, "feed", self.now, max_age_seconds=60))
        self.assertIsNone(validated_event_quote(
            100, self.observed, "feed", self.now, max_age_seconds=59))


if __name__ == "__main__":
    unittest.main()
