import unittest
from dipsaus_offline_cohort_gate import cohort_eligibility


def item(symbol):
    return dict(symbol=symbol, source="single-provider", adjustment_policy="adjusted_ohlcv",
                asof_cutoff="2018-03-27", corporate_actions_verified=True,
                benchmark_compatible_verified=True, license_reviewed=True,
                holdout_unseen=True)


class CohortGateTests(unittest.TestCase):
    def test_missing_provenance_blocks(self):
        result = cohort_eligibility([{"symbol": "AAPL"}, {"symbol": "MSFT"}])
        self.assertFalse(result["eligible"])

    def test_mixed_adjustment_policy_blocks(self):
        a, b = item("AAPL"), item("MSFT")
        b["adjustment_policy"] = "raw_ohlcv"
        self.assertIn("mixed_adjustment_policies", cohort_eligibility([a, b])["reasons"])

    def test_valid_attestations_are_not_independent_verification(self):
        result = cohort_eligibility([item("AAPL"), item("MSFT")])
        self.assertTrue(result["eligible"])
        self.assertFalse(result["independent_provenance_verified"])

    def test_reused_symbol_blocks(self):
        self.assertIn("record_1_duplicate_symbol",
                      cohort_eligibility([item("AAPL"), item("AAPL")])["reasons"])


if __name__ == "__main__":
    unittest.main()
