import unittest
from research_yearly_outlier_dependence import summarize_yearly_outlier_dependence


class OutlierDependenceTests(unittest.TestCase):
    def test_disagreement_and_missing_data(self):
        report = {"results": [{"symbol": "ABC", "years": [
            {"year": "2026",
             "positive": {"count": 12, "mean_pp": "3", "median_pp": "-1",
                          "mean_without_extremes_pp": "-0.5"},
             "negative": {"count": 11, "mean_pp": "1", "median_pp": "0",
                          "mean_without_extremes_pp": "0"}},
            {"year": "2025",
             "positive": {"count": 0, "mean_pp": None, "median_pp": None,
                          "mean_without_extremes_pp": None},
             "negative": {"count": 1, "mean_pp": "1", "median_pp": "1",
                          "mean_without_extremes_pp": None}}]}]}
        result = summarize_yearly_outlier_dependence(report)
        self.assertTrue(result["results"][0]["mean_median_sign_disagree"])
        self.assertTrue(result["results"][0]["mean_trimmed_sign_disagree"])
        self.assertEqual(result["results"][1]["status"], "insufficient_data")
        self.assertFalse(result["trade_ready"])


if __name__ == "__main__":
    unittest.main()
