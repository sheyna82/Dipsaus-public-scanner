"""Offline regression tests for event quote evidence validation."""
import unittest
from datetime import datetime, timezone, timedelta
from event_quote_evidence import validated_event_quote, event_quote_metrics
from event_opportunity_engine import classify_event_opportunities


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

    def test_valid_quote_only_clears_quote_requirement(self):
        metrics = {"issuer_confirmed_date": "2026-11-02"}
        metrics.update(event_quote_metrics(100, self.observed, "verified-feed", self.now))
        result = classify_event_opportunities("2026-11-02", self.now.date(), metrics)
        hold = next(x for x in result if x["stage"] == "EVENT_HOLD")
        self.assertNotIn("fresh_quote", hold["reason"])
        self.assertIn("implied_move_pct", hold["reason"])
        self.assertFalse(hold["eligible"])

    def test_invalid_quote_keeps_research_blocked(self):
        metrics = event_quote_metrics(100, "2026-11-02T14:50:00+00:00",
                                      "verified-feed", self.now)
        self.assertEqual(metrics, {})
        hold = next(x for x in classify_event_opportunities(
            "2026-11-02", self.now.date(), metrics) if x["stage"] == "EVENT_HOLD")
        self.assertIn("fresh_quote", hold["reason"])
        self.assertFalse(hold["eligible"])

    def test_custom_age_limit(self):
        self.assertIsNotNone(validated_event_quote(
            100, self.observed, "feed", self.now, max_age_seconds=60))
        self.assertIsNone(validated_event_quote(
            100, self.observed, "feed", self.now, max_age_seconds=59))


if __name__ == "__main__":
    unittest.main()
