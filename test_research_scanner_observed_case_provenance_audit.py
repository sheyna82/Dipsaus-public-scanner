"""Regression tests for dated observed notification provenance."""
import unittest
from research_scanner_observed_case_provenance_audit import audit_observed_cases


class ObservedCaseAuditTests(unittest.TestCase):
    def test_all_eight_observations_are_retained(self):
        result = audit_observed_cases()
        self.assertEqual(result["observation_count"], 8)
        self.assertEqual(result["signal_count"], 8)
        self.assertEqual(len(result["records"]), 8)

    def test_unverified_observations_are_not_reconstructed_trades(self):
        result = audit_observed_cases()
        self.assertEqual(result["reconstructable_signals"], 0)
        self.assertEqual(result["reconstructable_trades"], 0)

    def test_reasons_are_explicit(self):
        result = audit_observed_cases()
        for row in result["records"]:
            self.assertIn("unverified_decision_timestamp", row["reasons"])
            self.assertIn("execution_unverified", row["reasons"])
            self.assertIn("rule_version_unverified", row["reasons"])

    def test_signal_families_are_not_collapsed(self):
        result = audit_observed_cases()
        families = {r["family"] for r in result["records"]}
        self.assertEqual(families, {
            "EXIT_ZONE_REVIEW", "EARLY_RECOVERY",
            "BREAKOUT_HOLD_RETEST", "EU_ENTRY_RESEARCH"
        })


if __name__ == "__main__":
    unittest.main()
