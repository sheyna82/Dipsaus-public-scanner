"""No-network evaluation contract tests; reference independence is not asserted."""
import unittest
from datetime import datetime, timedelta, timezone
from research.us_setup_episode_evaluation import evaluate, optimal_episode_matches


def bars(prices):
    t = datetime(2026, 10, 1, 14, 30, tzinfo=timezone.utc)
    return [{"timestamp": (t + timedelta(minutes=i)).isoformat(),
             "low": p - 0.1, "close": p} for i, p in enumerate(prices)]


class EpisodeEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.data = bars([100, 99, 99.2, 99.6, 100.2, 100.5])
        self.when = self.data[4]["timestamp"]

    def test_perfect_one_to_one_match(self):
        result = evaluate("CSGP", self.data, [{"confirmed_utc": self.when, "source": "external_review"}])
        self.assertEqual((result["true_positive"], result["false_positive"], result["false_negative"]), (1, 0, 0))
        self.assertEqual((result["precision"], result["recall"]), (1, 1))
        self.assertFalse(result["notifications_allowed"])

    def test_unmatched_detection_counts_false_positive(self):
        result = evaluate("CSGP", self.data, [])
        self.assertEqual((result["true_positive"], result["false_positive"], result["false_negative"]), (0, 1, 0))

    def test_unmatched_reference_counts_false_negative(self):
        result = evaluate("CSGP", [], [{"confirmed_utc": self.when, "source": "external_review"}])
        self.assertEqual((result["true_positive"], result["false_positive"], result["false_negative"]), (0, 0, 1))

    def test_missing_source_fails_closed(self):
        with self.assertRaises(ValueError):
            evaluate("CSGP", self.data, [{"confirmed_utc": self.when}])

    def test_duplicate_reference_fails_closed(self):
        ref = {"confirmed_utc": self.when, "source": "external_review"}
        with self.assertRaises(ValueError):
            evaluate("CSGP", self.data, [ref, ref])


    def test_optimal_match_avoids_greedy_false_negative(self):
        t = datetime(2026, 10, 1, 14, 30, tzinfo=timezone.utc)
        # Detection at minute 4 is closer to reference minute 5, but
        # it must match minute 0 to leave minute 5 for the next detection.
        observed = [t + timedelta(minutes=4), t + timedelta(minutes=8)]
        references = [t, t + timedelta(minutes=5)]
        pairs = optimal_episode_matches(observed, references, 5 * 60)
        self.assertEqual([(i, j) for i, j, _ in pairs], [(0, 0), (1, 1)])

    def test_optimal_match_prefers_shorter_total_delay(self):
        t = datetime(2026, 10, 1, 14, 30, tzinfo=timezone.utc)
        observed = [t + timedelta(minutes=5)]
        references = [t, t + timedelta(minutes=6)]
        pairs = optimal_episode_matches(observed, references, 10 * 60)
        self.assertEqual([(i, j) for i, j, _ in pairs], [(0, 1)])

    def test_many_episodes_still_match_one_to_one(self):
        t = datetime(2026, 10, 1, 14, 30, tzinfo=timezone.utc)
        observed = [t + timedelta(minutes=10 * i) for i in range(200)]
        references = [x + timedelta(minutes=1) for x in observed]
        pairs = optimal_episode_matches(observed, references, 120)
        self.assertEqual(len(pairs), 200)
        self.assertEqual([(i, j) for i, j, _ in pairs], [(i, i) for i in range(200)])

    def test_matcher_rejects_oversized_grid(self):
        t = datetime(2026, 10, 1, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            optimal_episode_matches([t] * 1001, [t] * 1001, 60)

if __name__ == "__main__":
    unittest.main()
