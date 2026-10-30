import unittest
from dipsaus_offline_risk_cohorts import compare_risk_cohorts


def outcome(low, review=False):
    return {"research_only": True, "trade_ready": False,
            "source_attested_not_verified": True,
            "horizons": {5: {"worst_future_low_pct": low,
                             "large_gap_manual_review": review}}}


class RiskCohortTests(unittest.TestCase):
    def test_comparison_requires_sufficient_groups(self):
        result = compare_risk_cohorts([outcome(-8)] * 5, [outcome(-3)] * 5)
        self.assertTrue(result["minimum_sample_met"])
        self.assertEqual(result["difference_percentage_points"], -5)
        self.assertIsNone(result["order_instruction"])

    def test_missing_and_manual_review_are_counted(self):
        result = compare_risk_cohorts([outcome(-8, True), {"research_only": True,
            "trade_ready": False, "source_attested_not_verified": True, "horizons": {5: None}}],
            [outcome(-3)], min_per_group=1)
        self.assertEqual(result["warning_group"]["manual_review"], 1)
        self.assertEqual(result["warning_group"]["missing"], 1)
        self.assertFalse(result["minimum_sample_met"])
        self.assertIsNone(result["difference_percentage_points"])

    def test_rejects_invalid_parameters(self):
        self.assertIsNone(compare_risk_cohorts([], [], horizon=True))
        self.assertIsNone(compare_risk_cohorts([], [], min_per_group=0))


if __name__ == "__main__":
    unittest.main()
