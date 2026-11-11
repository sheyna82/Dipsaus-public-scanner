import unittest
from dipsaus_offline_signal_cohort import summarize_outcomes


def result(value=None, review=False):
    return {"research_only": True, "trade_ready": False,
            "data_provenance_independently_verified": False,
            "horizons": {5: None if value is None else {
                "estimated_net_close_return_pct": value,
                "manual_review_required": review}}}


class CohortTests(unittest.TestCase):
    def test_missing_and_review_remain_in_denominator(self):
        values = [result(4), result(-2), result(None), result(99, True), {"invalid": True}]
        summary = summarize_outcomes(values, 5)
        self.assertEqual(summary["nominated"], 5)
        self.assertEqual(summary["evaluated"], 2)
        self.assertEqual(summary["missing"], 1)
        self.assertEqual(summary["manual_review"], 1)
        self.assertEqual(summary["invalid"], 1)
        self.assertEqual(summary["coverage_pct"], 40.0)
        self.assertEqual(summary["mean_estimated_net_return_pct"], 1.0)
        self.assertEqual(summary["positive_share_pct"], 50.0)
        self.assertFalse(summary["trade_ready"])

    def test_empty_never_claims_performance(self):
        summary = summarize_outcomes([], 5)
        self.assertIsNone(summary["mean_estimated_net_return_pct"])
        self.assertIsNone(summary["positive_share_pct"])
        self.assertIsNone(summary["coverage_pct"])

    def test_invalid_values_are_not_silently_counted(self):
        for value in (float("nan"), float("inf"), True, "5"):
            summary = summarize_outcomes([result(value)], 5)
            self.assertEqual(summary["invalid"], 1)
            self.assertEqual(summary["evaluated"], 0)

    def test_invalid_horizon(self):
        self.assertIsNone(summarize_outcomes([], 0))
        self.assertIsNone(summarize_outcomes([], True))


if __name__ == "__main__":
    unittest.main()
