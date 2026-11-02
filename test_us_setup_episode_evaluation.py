"""No-network evaluation contract tests; reference independence is not asserted."""
import unittest
from datetime import datetime, timedelta, timezone
from research.us_setup_episode_evaluation import evaluate


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


if __name__ == "__main__":
    unittest.main()
