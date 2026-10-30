import unittest
from research_swing_event_classification import classify_event, deduplicate_events

BASE = {"symbol": "AMD", "event_id": "fy26q3", "published_at": "2026-11-03T21:00:00Z"}

class EventClassificationTests(unittest.TestCase):
    def test_calendar_is_not_material_or_trade_ready(self):
        result = classify_event({**BASE, "kind": "earnings_calendar"})
        self.assertEqual(result["stage"], "calendar")
        self.assertIsNone(result["impact_score"])
        self.assertFalse(result["trade_ready"])

    def test_release_is_material_but_not_buy_signal(self):
        result = classify_event({**BASE, "kind": "earnings_release", "surprise_pct": -12})
        self.assertEqual(result["stage"], "material")
        self.assertEqual(result["surprise_pct"], -12)
        self.assertIsNone(result["swing_score"])
        self.assertFalse(result["trade_ready"])

    def test_duplicate_alerts_are_combined(self):
        event = {**BASE, "kind": "earnings_calendar"}
        self.assertEqual(len(deduplicate_events([event, dict(event)])), 1)

    def test_distinct_releases_are_retained(self):
        first = {**BASE, "kind": "earnings_calendar"}
        second = {**BASE, "kind": "earnings_release"}
        self.assertEqual(len(deduplicate_events([first, second])), 2)

    def test_missing_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing_event_identity"):
            classify_event({"symbol": "AMD", "kind": "earnings_release"})

    def test_nonfinite_surprise_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_surprise"):
            classify_event({**BASE, "kind": "earnings_release", "surprise_pct": float("nan")})

if __name__ == "__main__":
    unittest.main()
