import unittest
from dipsaus_offline_adjustment_gate import assess_cross_provider_comparison


class AdjustmentGateTests(unittest.TestCase):
    def test_observed_aapl_spy_mismatch_blocks(self):
        audit = {"raw_ohlc_cross_provider_comparison_caution": True,
                 "adjustment_compatibility_verified": False}
        self.assertEqual(assess_cross_provider_comparison(audit)["reason"],
                         "unresolved_adjustment_mismatch")

    def test_missing_verification_blocks(self):
        self.assertEqual(assess_cross_provider_comparison({})["status"], "BLOCKED")

    def test_verified_adjustments_still_not_trade_ready(self):
        result = assess_cross_provider_comparison({
            "adjustment_compatibility_verified": True,
            "historical_earnings_verified": True})
        self.assertEqual(result["status"], "RESEARCH_ONLY")
        self.assertFalse(result["trade_ready"])


if __name__ == "__main__":
    unittest.main()
