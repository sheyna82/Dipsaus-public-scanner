import unittest
from research_notification_family_net_comparison import compare_signal_families

def sample(**kw):
    row = dict(cohort_id="2026-01-02", symbol="AAA", horizon=3,
               family="MOMENTUM_NEAR_HIGH", entry_date="2026-01-05",
               exit_date="2026-01-07", outcome_verified=True, net_return_pct=2.0)
    row.update(kw)
    return row

class FamilyNetComparisonTests(unittest.TestCase):
    def test_matched_cohorts(self):
        result = compare_signal_families([sample(), sample(symbol="BBB", net_return_pct=-1)])
        self.assertEqual(result["summaries"][0]["mean_net_pct"], 0.5)
        self.assertFalse(result["profitability_ranking_available"])
    def test_unverified_rejected(self):
        with self.assertRaises(ValueError):
            compare_signal_families([sample(outcome_verified=False)])
    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            compare_signal_families([sample(), sample()])
    def test_missing_outcomes_not_zero(self):
        self.assertEqual(compare_signal_families([])["summaries"], [])
    def test_horizon_rejected(self):
        with self.assertRaises(ValueError):
            compare_signal_families([sample(horizon=4)])
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            compare_signal_families([sample(net_return_pct=float("nan"))])

if __name__ == "__main__":
    unittest.main()
