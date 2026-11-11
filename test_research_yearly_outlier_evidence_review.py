import unittest
from research_yearly_outlier_evidence_review import yearly_outlier_evidence_review


class EvidenceReviewTests(unittest.TestCase):
    def test_consistent_but_small_cohort_not_approved(self):
        source = {"results": [{"symbol": "META", "year": "2026",
            "status": "descriptive_only", "positive_count": 29, "negative_count": 38,
            "mean_difference_pp": "2.63", "median_difference_pp": "2.36",
            "trimmed_difference_pp": "2.65"}]}
        result = yearly_outlier_evidence_review(source)
        row = result["results"][0]
        self.assertTrue(row["all_three_directions_agree"])
        self.assertFalse(row["group_sizes_sufficient"])
        self.assertEqual(row["interpretation"], "small_group")
        self.assertFalse(result["trade_ready"])

    def test_direction_disagreement(self):
        source = {"results": [{"symbol": "AMD", "year": "2025",
            "status": "descriptive_only", "positive_count": 42, "negative_count": 42,
            "mean_difference_pp": "0.24", "median_difference_pp": "-2.05",
            "trimmed_difference_pp": "-0.15"}]}
        row = yearly_outlier_evidence_review(source)["results"][0]
        self.assertEqual(row["interpretation"], "outlier_sensitive")

    def test_invalid_threshold(self):
        with self.assertRaisesRegex(ValueError, "invalid_minimum_per_group"):
            yearly_outlier_evidence_review({}, minimum_per_group=0)


if __name__ == "__main__":
    unittest.main()
