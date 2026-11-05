"""Synthetic prospective ranking evaluation tests."""
import unittest
from research_swing_rank_validation import evaluate_ranked_outcomes


def row(day, ticker, score, ret, **changes):
    x = {"entry_day": day, "recorded_day": day,
         "outcome_day": "2026-11-20", "ticker": ticker,
         "score": score, "net_return_pct": ret, "eligible": True}
    x.update(changes)
    return x


class RankValidationTests(unittest.TestCase):
    def test_top_beats_bottom_descriptively(self):
        rows = [row("2026-11-02", "A", 10, 5),
                row("2026-11-02", "B", 1, -2)]
        result = evaluate_ranked_outcomes(rows, min_days=2, min_rows=2)
        self.assertEqual(result["mean_top_minus_bottom_pct_points"], "7")
        self.assertFalse(result["predictive_edge_proven"])
        self.assertFalse(result["evidence_sufficient_for_review"])

    def test_duplicate_rejected(self):
        a = row("2026-11-02", "A", 10, 5)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            evaluate_ranked_outcomes([a, a])

    def test_future_recording_rejected(self):
        with self.assertRaisesRegex(ValueError, "lookahead"):
            evaluate_ranked_outcomes([row("2026-11-02", "A", 10, 5,
                                          recorded_day="2026-11-03")])

    def test_outcome_must_follow_entry(self):
        with self.assertRaisesRegex(ValueError, "lookahead"):
            evaluate_ranked_outcomes([row("2026-11-02", "A", 10, 5,
                                          outcome_day="2026-11-02")])

    def test_ineligible_excluded(self):
        result = evaluate_ranked_outcomes([
            row("2026-11-02", "A", 10, 5),
            row("2026-11-02", "B", 1, -2, eligible=False)])
        self.assertEqual(result["eligible_rows"], 1)
        self.assertEqual(result["paired_days"], 0)

    def test_equal_groups_on_odd_count(self):
        result = evaluate_ranked_outcomes([
            row("2026-11-02", "A", 3, 6),
            row("2026-11-02", "B", 2, 100),
            row("2026-11-02", "C", 1, -4)])
        self.assertEqual(result["mean_top_minus_bottom_pct_points"], "10")

    def test_minimum_sample_flag(self):
        rows = []
        for d in range(2, 12):
            day = f"2026-11-{d:02d}"
            rows += [row(day, "A", 2, 2), row(day, "B", 1, 1)]
        result = evaluate_ranked_outcomes(rows, min_days=10, min_rows=20)
        self.assertTrue(result["evidence_sufficient_for_review"])
        self.assertFalse(result["predictive_edge_proven"])


if __name__ == "__main__":
    unittest.main()
