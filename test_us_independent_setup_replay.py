"""Isolated replay tests. No market network, ntfy, or broker integration."""
import unittest
from datetime import datetime, timedelta, timezone
from research.us_independent_setup_replay import replay


def bars(prices):
    start = datetime(2026, 10, 1, 14, 30, tzinfo=timezone.utc)
    return [{"timestamp": (start + timedelta(minutes=i)).isoformat(),
             "low": round(p - .1, 4), "close": p} for i, p in enumerate(prices)]


class ResearchSetupReplayTests(unittest.TestCase):
    def test_single_recovery_leg_not_repeated(self):
        data = bars([100, 99, 99.2, 99.5, 100, 100.4, 101, 101.2, 101.5])
        self.assertEqual(len(replay("CSGP", data)), 1)

    def test_new_episode_requires_reset_below_previous_anchor(self):
        data = bars([100, 99, 99.2, 99.6, 100.2, 100.5, 99.1, 99.3, 99.6,
                     100.1, 97.7, 97.9, 98.2, 98.7, 99.1])
        events = replay("CSGP", data)
        self.assertEqual(len(events), 2)
        self.assertNotEqual(events[0]["candidate_setup_id"], events[1]["candidate_setup_id"])

    def test_prefix_invariance(self):
        data = bars([100, 99, 99.2, 99.6, 100.2, 100.5, 97.7, 97.9, 98.2, 98.7, 99.1])
        full = replay("CSGP", data)
        for end in range(1, len(data) + 1):
            prefix = replay("CSGP", data[:end])
            self.assertEqual(prefix, [e for e in full if e["confirmed_utc"] <= data[end - 1]["timestamp"]])

    def test_invalid_and_duplicate_timestamps_fail_closed(self):
        data = bars([100, 99, 99.2])
        data[2]["timestamp"] = data[1]["timestamp"]
        with self.assertRaises(ValueError):
            replay("CSGP", data)
        with self.assertRaises(ValueError):
            replay("CSGP", [{"timestamp": "2026-10-01T10:00:00", "low": 9, "close": 10}])

    def test_replay_never_qualifies_phone_alert(self):
        result = replay("CSGP", bars([100, 99, 99.2, 99.6, 100.2]))
        self.assertTrue(result)
        self.assertTrue(all(e["research_only"] and not e["notification_eligible"]
                            and not e["independent_setup_verified"] for e in result))


if __name__ == "__main__":
    unittest.main()
