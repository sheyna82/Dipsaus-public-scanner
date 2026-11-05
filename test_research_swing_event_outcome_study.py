"""Regression tests for point-in-time event outcome study."""
import unittest
from research_swing_event_outcome_study import study_event_outcomes

SESSIONS = [
    {"open_at": f"2026-10-{day:02d}T09:30:00-04:00",
     "close_at": f"2026-10-{day:02d}T16:00:00-04:00"}
    for day in (26, 27, 28, 29, 30)
]
BARS = [{"open": p, "low": p - 1} for p in (100, 101, 103, 102, 105)]
def event(at, verified=True):
    return {"symbol": "TEST", "event_id": "1", "kind": "earnings_release",
            "source": "fixture", "published_at": at, "first_observed_at": at,
            "release_timestamp_verified": verified}

class EventOutcomeStudyTests(unittest.TestCase):
    def test_preopen_event_uses_next_open(self):
        result = study_event_outcomes(event("2026-10-26T08:00:00-04:00"),
                                      SESSIONS, BARS, horizons=(3,))
        self.assertEqual(result["outcomes"][0]["entry_index"], 1)
        self.assertEqual(result["outcomes"][0]["exit_index"], 4)
        self.assertFalse(result["trade_ready"])
    def test_after_close_uses_later_open(self):
        result = study_event_outcomes(event("2026-10-26T16:01:00-04:00"),
                                      SESSIONS, BARS, horizons=(2,))
        self.assertEqual(result["outcomes"][0]["entry_index"], 2)
    def test_insufficient_future_sessions(self):
        result = study_event_outcomes(event("2026-10-29T16:01:00-04:00"),
                                      SESSIONS, BARS)
        self.assertEqual(result["outcomes"], [])
    def test_unverified_news_rejected(self):
        with self.assertRaisesRegex(ValueError, "unverified_release_time"):
            study_event_outcomes(event("2026-10-26T08:00:00-04:00", False),
                                 SESSIONS, BARS)
    def test_mismatched_price_series_rejected(self):
        with self.assertRaisesRegex(ValueError, "session_bar_length_mismatch"):
            study_event_outcomes(event("2026-10-26T08:00:00-04:00"),
                                 SESSIONS, BARS[:-1])

if __name__ == "__main__":
    unittest.main()
