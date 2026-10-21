import unittest
from dipsaus_offline_recovery_baseline import score_recovery_candidate


def features(**changes):
    data = {"relative_strength_20d": 3.0, "return_5d": 2.0,
            "volume_ratio_20d": 1.5, "atr_pct": 3.0,
            "market_return_5d": 1.0, "days_to_earnings": 12}
    data.update(changes)
    return data


class RecoveryBaselineTests(unittest.TestCase):
    def test_positive_candidate_has_no_probability_or_order(self):
        r = score_recovery_candidate(features())
        self.assertEqual(r["decision"], "RESEARCH_CANDIDATE")
        self.assertEqual(r["score"], 7)
        self.assertIsNone(r["probability"])
        self.assertIsNone(r["order_instruction"])
        self.assertFalse(r["trade_ready"])

    def test_weak_candidate(self):
        r = score_recovery_candidate(features(relative_strength_20d=-5,
                return_5d=-9, volume_ratio_20d=0.4, atr_pct=9,
                market_return_5d=-5))
        self.assertEqual(r["decision"], "NO_CANDIDATE")

    def test_imminent_earnings_abstains(self):
        self.assertEqual(score_recovery_candidate(
            features(days_to_earnings=2))["reason"], "imminent_earnings")

    def test_missing_and_invalid_data_abstains(self):
        self.assertEqual(score_recovery_candidate(
            features(atr_pct=float("nan")))["decision"], "ABSTAIN")
        self.assertEqual(score_recovery_candidate(
            features(volume_ratio_20d=0))["reason"], "invalid_feature_range")
        self.assertEqual(score_recovery_candidate(
            features(days_to_earnings=-1))["decision"], "ABSTAIN")

    def test_boundary_earnings_four_days_allowed(self):
        self.assertEqual(score_recovery_candidate(
            features(days_to_earnings=4))["decision"], "RESEARCH_CANDIDATE")


if __name__ == "__main__":
    unittest.main()
