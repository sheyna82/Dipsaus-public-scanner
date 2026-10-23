import unittest
from dipsaus_offline_multiticker_readiness import (
    REQUIRED, assess_multiticker_readiness,
)


class MultitickerReadinessTests(unittest.TestCase):
    def test_empty_evidence_blocks(self):
        result = assess_multiticker_readiness({})
        self.assertEqual(result["status"], "DATA_BLOCKED")
        self.assertEqual(set(result["missing_or_unverified"]), set(REQUIRED))
        self.assertFalse(result["trade_ready"])

    def test_price_only_is_not_full_score(self):
        result = assess_multiticker_readiness({
            "adjusted_ohlcv_corporate_actions": True,
            "benchmark_compatible_history": True,
        })
        self.assertIn("point_in_time_earnings_calendar", result["missing_or_unverified"])
        self.assertIn("delisted_stock_coverage", result["missing_or_unverified"])
        self.assertTrue(result["price_only_four_event_rule_is_not_equivalent"])

    def test_complete_attestations_still_require_independent_audit(self):
        result = assess_multiticker_readiness(dict.fromkeys(REQUIRED, True))
        self.assertEqual(result["status"], "READY_FOR_INDEPENDENT_AUDIT")
        self.assertFalse(result["independent_data_audit_completed"])
        self.assertFalse(result["predictive_edge_proven"])
        self.assertFalse(result["trade_ready"])

    def test_invalid_evidence_is_blocked(self):
        self.assertEqual(assess_multiticker_readiness(None)["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
