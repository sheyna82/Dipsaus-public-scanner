"""Regression tests for observed-cohort role separation."""
import unittest
from research_scanner_observed_cohort_eligibility import classify_observed_cohort
from research_notification_signal_cases import SignalCase


class ObservedCohortEligibilityTests(unittest.TestCase):
    def test_original_observations_separate_exit_from_entry(self):
        result = classify_observed_cohort()
        self.assertEqual(result["observations"], 8)
        self.assertEqual(result["role_counts"]["existing_position_exit_review"], 1)
        self.assertEqual(result["role_counts"]["candidate_entry_research"], 7)
        self.assertEqual(result["return_study_eligible"], 0)

    def test_exit_review_never_becomes_entry_candidate(self):
        result = classify_observed_cohort((
            SignalCase("EXE", "EXIT_ZONE_REVIEW", "13:51", "exit"),
        ))
        self.assertEqual(result["rows"][0]["role"], "existing_position_exit_review")
        self.assertFalse(result["rows"][0]["verified_trade"])

    def test_unknown_family_fails_closed(self):
        result = classify_observed_cohort((
            SignalCase("TEST", "UNRECOGNIZED", "12:00", "unknown"),
        ))
        self.assertEqual(result["rows"][0]["role"], "unknown_family_excluded")
        self.assertEqual(result["return_study_eligible"], 0)


if __name__ == "__main__":
    unittest.main()
