"""Regression checks for conservative event-to-session alignment."""
import unittest
from research_swing_event_session_alignment import align_event_to_sessions

SESSIONS = [
    {"open_at": "2026-10-27T09:30:00-04:00", "close_at": "2026-10-27T16:00:00-04:00"},
    {"open_at": "2026-10-28T09:30:00-04:00", "close_at": "2026-10-28T16:00:00-04:00"},
]
def event(at, verified=True):
    return {"symbol": "TEST", "event_id": "release-1", "kind": "earnings_release",
            "source": "fixture", "published_at": at, "first_observed_at": at,
            "release_timestamp_verified": verified}

class SessionAlignmentTests(unittest.TestCase):
    def test_before_open_maps_to_same_session_close(self):
        self.assertEqual(align_event_to_sessions(event("2026-10-27T08:00:00-04:00"), SESSIONS)["known_session_index"], 0)
    def test_after_close_maps_to_next_session(self):
        self.assertEqual(align_event_to_sessions(event("2026-10-27T16:01:00-04:00"), SESSIONS)["known_session_index"], 1)
    def test_processing_delay_can_shift_decision(self):
        self.assertEqual(align_event_to_sessions(event("2026-10-27T15:59:59-04:00"), SESSIONS, decision_lag_seconds=2)["known_session_index"], 1)
    def test_unverified_release_rejected(self):
        with self.assertRaisesRegex(ValueError, "unverified_release_time"):
            align_event_to_sessions(event("2026-10-27T08:00:00-04:00", False), SESSIONS)
    def test_no_future_session(self):
        self.assertIsNone(align_event_to_sessions(event("2026-10-29T08:00:00-04:00"), SESSIONS))
    def test_overlapping_sessions_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_session_order"):
            align_event_to_sessions(event("2026-10-29T08:00:00-04:00"), SESSIONS + [SESSIONS[1]])
    def test_negative_delay_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_decision_lag"):
            align_event_to_sessions(event("2026-10-27T08:00:00-04:00"), SESSIONS, decision_lag_seconds=-1)

if __name__ == "__main__":
    unittest.main()
