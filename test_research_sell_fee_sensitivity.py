import unittest
from research_sell_fee_sensitivity import assess_sell_fee_uncertainty as assess

BASE = dict(ask=65, bid=64.99, invalidation=64, target=70,
            budget_eur=3500, buy_fee_eur=4.9, fx_eur_per_unit=1,
            buy_slippage_per_share=0, sell_slippage_per_share=0)

class SellFeeSensitivityTests(unittest.TestCase):
    def test_equal_ceiling_remains_unverified(self):
        r = assess(sell_fee_estimate_eur=4.9, sell_fee_ceiling_eur=4.9,
                   scenario_inputs=BASE)
        self.assertEqual(r["status"], "CONSERVATIVE_RESEARCH_THRESHOLDS_MET")
        self.assertFalse(r["sell_fee_ceiling_independently_verified"])
        self.assertFalse(r["trade_ready"])

    def test_higher_fee_can_disqualify_profit(self):
        r = assess(sell_fee_estimate_eur=4.9, sell_fee_ceiling_eur=200,
                   scenario_inputs=BASE)
        self.assertEqual(r["status"], "CONSERVATIVE_RESEARCH_THRESHOLDS_FAILED")
        self.assertLess(r["conservative_net_profit_eur"], r["baseline_net_profit_eur"])

    def test_ceiling_below_estimate_blocks(self):
        r = assess(sell_fee_estimate_eur=5, sell_fee_ceiling_eur=4,
                   scenario_inputs=BASE)
        self.assertEqual(r["reason"], "CEILING_BELOW_ESTIMATE")

    def test_missing_ceiling_blocks(self):
        r = assess(sell_fee_estimate_eur=5, sell_fee_ceiling_eur=None,
                   scenario_inputs=BASE)
        self.assertEqual(r["reason"], "INVALID_FEE_BOUNDS")

    def test_nan_ceiling_blocks(self):
        r = assess(sell_fee_estimate_eur=5, sell_fee_ceiling_eur=float("nan"),
                   scenario_inputs=BASE)
        self.assertEqual(r["reason"], "INVALID_FEE_BOUNDS")

    def test_cannot_force_verified_evidence(self):
        r = assess(sell_fee_estimate_eur=4.9, sell_fee_ceiling_eur=6,
                   scenario_inputs={**BASE, "evidence_verified": True})
        self.assertEqual(r["reason"], "CONFLICTING_SCENARIO_FIELDS")

    def test_noncomputable_scenario_blocks(self):
        r = assess(sell_fee_estimate_eur=4.9, sell_fee_ceiling_eur=6,
                   scenario_inputs={**BASE, "target": 64})
        self.assertEqual(r["reason"], "SCENARIO_NOT_COMPUTABLE")

if __name__ == "__main__":
    unittest.main()
