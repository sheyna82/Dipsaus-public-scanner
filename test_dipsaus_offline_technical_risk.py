import unittest
from dipsaus_offline_technical_risk import assess_risk, research_optional_stop_reference, research_profit_protection_reference, research_pullback_context, research_consolidated_risk, research_alert_transition

class RiskTests(unittest.TestCase):
    def setUp(self):
        self.bars = [{"high": 101+i, "low": 99+i, "close": 100+i} for i in range(20)]

    def test_risk_calculation(self):
        r = assess_risk(self.bars, 118, 130)
        self.assertEqual(r["technical_invalidation_reference"], 108)
        self.assertAlmostEqual(r["risk_reward"], 12/10, places=4)
        self.assertFalse(r["trade_ready"])
        self.assertIsNone(r["order_instruction"])

    def test_trend_break_detected(self):
        bars = list(self.bars)
        bars[-1] = {"high": 111, "low": 105, "close": 106}
        r = assess_risk(bars, 118)
        self.assertTrue(r["trend_break_below_previous_10_bar_low"])

    def test_volatility_expansion(self):
        bars = [{"high": 101, "low": 99, "close": 100} for _ in range(30)]
        for bar in bars[-14:]:
            bar.update(high=105, low=95)
        r = assess_risk(bars, 100)
        self.assertTrue(r["volatility_expansion_1_5x"])

    def test_insufficient_history_for_volatility_comparison(self):
        self.assertIsNone(assess_risk(self.bars, 118)["volatility_expansion_1_5x"])

    def test_duplicate_and_unordered_dates_rejected(self):
        bars = [dict(b, date=f"2026-09-{i+1:02d}") for i, b in enumerate(self.bars)]
        self.assertIsNotNone(assess_risk(bars, 118))
        bars[-1]["date"] = bars[-2]["date"]
        self.assertIsNone(assess_risk(bars, 118))
        bars[-1]["date"] = "not-a-date"
        self.assertIsNone(assess_risk(bars, 118))

    def test_partial_dates_rejected(self):
        bars = list(self.bars)
        bars[0] = dict(bars[0], date="2026-09-01")
        self.assertIsNone(assess_risk(bars, 118))

    def test_optional_reference_is_not_order(self):
        result = research_optional_stop_reference(self.bars, 118)
        self.assertEqual(result["atr_buffer_reference"], 114)
        self.assertEqual(result["structural_reference"], 108)
        self.assertFalse(result["stop_order_proposed"])
        self.assertIsNone(result["order_instruction"])
        self.assertFalse(result["trade_ready"])
        self.assertIn("may not fill", result["warning"])

    def test_optional_reference_rejects_unsafe_inputs(self):
        self.assertIsNone(research_optional_stop_reference(self.bars, 118, atr_multiplier=0))
        self.assertIsNone(research_optional_stop_reference(self.bars, 118, atr_multiplier=float("nan")))
        self.assertIsNone(research_optional_stop_reference(self.bars, 108))
        self.assertIsNone(research_optional_stop_reference(self.bars, 2, atr_multiplier=2))

    def test_profit_protection_activation_and_monotonicity(self):
        fn = research_profit_protection_reference
        self.assertFalse(fn(100, 104, 2)["active"])
        first = fn(100, 110, 2)
        self.assertEqual(first["reference"], 106)
        later = fn(100, 108, 2, previous_reference=106)
        self.assertEqual(later["reference"], 106)
        self.assertIsNone(later["order_instruction"])
        self.assertFalse(later["trade_ready"])

    def test_profit_protection_invalid_inputs(self):
        fn = research_profit_protection_reference
        self.assertIsNone(fn(100, 110, 0))
        self.assertIsNone(fn(100, 110, float("inf")))
        self.assertIsNone(fn(100, 110, 2, previous_reference=-1))

    def test_pullback_context_distinguishes_normal_and_break(self):
        stable = [{"high": 101, "low": 99, "close": 100} for _ in range(30)]
        self.assertEqual(research_pullback_context(stable)["context"], "within_one_atr")
        broken = list(stable)
        broken[-1] = {"high": 99, "low": 94, "close": 95}
        result = research_pullback_context(broken)
        self.assertEqual(result["context"], "structural_break")
        self.assertIsNone(result["order_instruction"])

    def test_pullback_context_invalid_input(self):
        self.assertIsNone(research_pullback_context([]))
        self.assertIsNone(research_pullback_context(self.bars[:4]))

    def test_prior_support_not_contaminated_by_current_bar(self):
        bars = list(self.bars)
        bars[-1] = {"high": 111, "low": 90, "close": 95}
        risk = assess_risk(bars, 118)
        self.assertEqual(risk["technical_invalidation_reference"], 108)
        self.assertTrue(risk["trend_break_below_previous_10_bar_low"])

    def test_profit_protection_rejects_impossible_peak(self):
        self.assertIsNone(research_profit_protection_reference(100, 90, 2))

    def test_overnight_gap_warning(self):
        bars = [{"high": 101, "low": 99, "close": 100} for _ in range(20)]
        bars[-1] = {"open": 90, "high": 101, "low": 89, "close": 100}
        risk = assess_risk(bars, 100)
        self.assertTrue(risk["overnight_gap_warning_1_5x_atr"])
        self.assertGreater(risk["overnight_gap_atr_units"], 1.5)
        self.assertIsNone(risk["order_instruction"])

    def test_invalid_last_open_rejected(self):
        bars = list(self.bars)
        bars[-1] = dict(bars[-1], open=200)
        self.assertIsNone(assess_risk(bars, 118))

    def test_gap_unavailable_without_open(self):
        self.assertIsNone(assess_risk(self.bars, 118)["overnight_gap_warning_1_5x_atr"])

    def test_consolidated_priority_deduplicates_reasons(self):
        bars = [{"high": 101, "low": 99, "close": 100} for _ in range(30)]
        bars[-1] = {"open": 90, "high": 99, "low": 89, "close": 95}
        result = research_consolidated_risk(bars)
        self.assertEqual(result["priority"], "structural_break")
        self.assertIn("large_overnight_gap", result["reasons"])
        self.assertTrue(result["single_summary"])
        self.assertFalse(result["notification_sent"])
        self.assertIsNone(result["order_instruction"])

    def test_consolidated_routine_and_invalid(self):
        bars = [{"high": 101, "low": 99, "close": 100} for _ in range(30)]
        self.assertEqual(research_consolidated_risk(bars)["priority"], "routine")
        self.assertIsNone(research_consolidated_risk([]))

    def test_duplicate_risk_does_not_repeat(self):
        state = {"priority": "large_gap", "reasons": ["large_overnight_gap"]}
        r = research_alert_transition(state, state)
        self.assertFalse(r["suggest_review"])
        self.assertTrue(r["duplicate_suppressed"])

    def test_new_risk_reason_gets_attention(self):
        old = {"priority": "large_gap", "reasons": ["large_overnight_gap"]}
        new = {"priority": "structural_break",
               "reasons": ["large_overnight_gap", "prior_support_broken"]}
        r = research_alert_transition(old, new)
        self.assertTrue(r["suggest_review"])
        self.assertTrue(r["priority_escalated"])
        self.assertEqual(r["new_reasons"], ["prior_support_broken"])
        self.assertFalse(r["notification_sent"])

    def test_routine_does_not_trigger(self):
        self.assertFalse(research_alert_transition(None, {"priority": "routine", "reasons": []})["suggest_review"])

    def test_stoploss_advice_cannot_be_enabled(self):
        self.assertIsNone(assess_risk(self.bars, 118, stoploss_advice=True))

    def test_invalid_data_rejected(self):
        self.assertIsNone(assess_risk(self.bars[:14], 118))
        self.assertIsNone(assess_risk(self.bars, float("nan")))
        self.assertIsNone(assess_risk(self.bars, 118, period=True))

    def test_no_positive_reward(self):
        self.assertIsNone(assess_risk(self.bars, 118, 0))
        self.assertIsNone(assess_risk(self.bars, 118, 110)["risk_reward"])

if __name__ == "__main__":
    unittest.main()
