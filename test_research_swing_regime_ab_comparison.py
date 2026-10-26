import unittest
from research_swing_regime_ab_comparison import compare_regime_gating

class RegimeABTests(unittest.TestCase):
    def test_gate_skips_and_counts_cash(self):
        rows = [{"decision_date": "2026-01-01", "symbol": "AAA", "horizon": 5,
                 "net_return_pct": -8.0, "index_closes": [100.0]*60 + [99-i for i in range(20)]},
                {"decision_date": "2026-01-02", "symbol": "BBB", "horizon": 10,
                 "net_return_pct": 2.0, "index_closes": [100+i*.1 for i in range(80)]}]
        r = compare_regime_gating(rows)
        self.assertEqual(r["skipped"], 1)
        self.assertEqual(r["mean_gated_cash_adjusted_pct"], 1.0)
        self.assertEqual(r["mean_ungated_net_pct"], -3.0)
    def test_duplicate_rejected(self):
        row = {"decision_date": "2026-01-01", "symbol": "AAA", "horizon": 5,
               "net_return_pct": 1.0, "index_closes": [100.0]*80}
        with self.assertRaises(ValueError):
            compare_regime_gating([row,row])
    def test_no_unapproved_horizon(self):
        with self.assertRaises(ValueError):
            compare_regime_gating([{"decision_date": "2026-01-01", "symbol": "AAA",
                "horizon": 40, "net_return_pct": 1.0, "index_closes": [100.0]*80}])
if __name__ == "__main__":
    unittest.main()
