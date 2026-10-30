import unittest
from dipsaus_offline_recovery_score_report import summarize_recovery_scores


def item(i, score, status):
    return {"id": str(i), "score": score, "status": status}


class ScoreReportTests(unittest.TestCase):
    def test_unresolved_cases_counted_in_coverage(self):
        records = [item("a", 7, "GAIN_FIRST"),
                   item("b", 6, "AMBIGUOUS_SAME_BAR"),
                   item("c", 5, "INSUFFICIENT_FUTURE_DATA")]
        r = summarize_recovery_scores(records, minimum_resolved=1)
        high = r["bands"]["high"]
        self.assertEqual(high["nominated"], 3)
        self.assertEqual(high["resolved"], 1)
        self.assertEqual(high["coverage_pct"], 33.33)
        self.assertEqual(high["gain_first_rate_pct"], 100)
        self.assertFalse(r["probabilities_calibrated"])

    def test_small_samples_suppress_rates(self):
        r = summarize_recovery_scores([item("a", 6, "GAIN_FIRST")])
        self.assertIsNone(r["bands"]["high"]["gain_first_rate_pct"])
        self.assertFalse(r["bands"]["high"]["minimum_resolved_met"])

    def test_band_separation(self):
        records = [item("a", 7, "LOSS_FIRST"), item("b", 4, "TIMEOUT"),
                   item("c", 0, "GAIN_FIRST")]
        r = summarize_recovery_scores(records, minimum_resolved=1)
        self.assertEqual([r["bands"][k]["nominated"] for k in ("high", "medium", "low")],
                         [1, 1, 1])

    def test_duplicate_or_invalid_rejected(self):
        self.assertIsNone(summarize_recovery_scores(
            [item("a", 7, "GAIN_FIRST"), item("a", 5, "LOSS_FIRST")]))
        self.assertIsNone(summarize_recovery_scores([item("a", 8, "GAIN_FIRST")]))
        self.assertIsNone(summarize_recovery_scores([item("a", 5, "UNKNOWN")]))


if __name__ == "__main__":
    unittest.main()
