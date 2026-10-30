"""Synthetic tests for dated swing exit cohort aggregation."""
import unittest
from decimal import Decimal
from research_swing_exit_cohort_validation import summarize_policy_cohorts


def cohort(id_, entry, exit_, fixed=10, target=20, trail=15):
    return {"cohort_id": id_, "entry_date": entry, "last_exit_date": exit_,
            "policies": {"fixed_horizon": fixed,
                         "close_target_next_open": target,
                         "close_trailing_next_open": trail}}


class CohortValidationTests(unittest.TestCase):
    def test_disjoint_cohorts(self):
        result = summarize_policy_cohorts([
            cohort("A", "2026-11-02", "2026-11-06"),
            cohort("B", "2026-11-09", "2026-11-13", -5, 2, 0)])
        self.assertEqual(result["overlapping_cohort_count"], 0)
        self.assertEqual(Decimal(result["results"]["fixed_horizon"]["aggregate_net_pnl"]), 5)
        self.assertFalse(result["independent_trials_established"])

    def test_overlapping_windows_flagged(self):
        result = summarize_policy_cohorts([
            cohort("A", "2026-11-02", "2026-11-09"),
            cohort("B", "2026-11-05", "2026-11-12")])
        self.assertEqual(result["overlapping_cohort_ids"], ["B"])

    def test_duplicate_cohort_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_or_invalid"):
            summarize_policy_cohorts([
                cohort("A", "2026-11-02", "2026-11-06"),
                cohort("A", "2026-11-09", "2026-11-13")])

    def test_missing_policy_rejected(self):
        x = cohort("A", "2026-11-02", "2026-11-06")
        del x["policies"]["close_trailing_next_open"]
        with self.assertRaisesRegex(ValueError, "unmatched_policies"):
            summarize_policy_cohorts([x])

    def test_invalid_window_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_cohort_window"):
            summarize_policy_cohorts([cohort("A", "2026-11-06", "2026-11-02")])

    def test_nonfinite_pnl_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_net_pnl"):
            summarize_policy_cohorts([
                cohort("A", "2026-11-02", "2026-11-06", float("nan"))])


if __name__ == "__main__":
    unittest.main()
