import unittest
from decimal import Decimal
from research.swing_lifecycle.synthetic_warning_exit_smoke import synthetic_warning_exit_smoke_report


class SyntheticWarningExitSmokeTests(unittest.TestCase):
    def test_end_to_end_both_partitions(self):
        report = synthetic_warning_exit_smoke_report()
        self.assertEqual(report["dataset"], "synthetic_not_historical")
        self.assertEqual(report["scenarios"], 4)
        self.assertEqual(report["result"]["training"]["trade_candidates"], 2)
        self.assertEqual(report["result"]["holdout"]["trade_candidates"], 2)
        self.assertEqual(report["result"]["purged_crossing_or_near_cutoff"], 0)
        self.assertFalse(report["historical_edge_proven"])

    def test_both_partitions_capture_rebound_and_decline(self):
        result = synthetic_warning_exit_smoke_report()["result"]
        for partition in ("training", "holdout"):
            data = result[partition]
            self.assertEqual(data["warning_candidates"], 2)
            differences = [
                Decimal(x["counterfactual_baseline_minus_candidate_pct_points"])
                for x in data["result"]["candidate_diagnostics"]]
            self.assertTrue(any(x > 0 for x in differences))
            self.assertTrue(any(x < 0 for x in differences))


if __name__ == "__main__":
    unittest.main()
