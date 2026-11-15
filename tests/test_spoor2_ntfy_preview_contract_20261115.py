"""Synthetic offline preview checks; no ntfy network transport."""
import unittest
from research.spoor2_ntfy_preview_contract_20261115 import build_offline_ntfy_preview


class NtfyPreviewContractTests(unittest.TestCase):
    def example(self, **overrides):
        args = dict(entry_low="49.50", entry_high="50", invalidation="47.50",
                    target="55", rr="2", net_profit_eur="340.20",
                    buy_fee_eur="4.90", sell_fee_eur="4.90")
        args.update(overrides)
        return build_offline_ntfy_preview("DEMO", "BREAKOUT-SEEN", **args)

    def test_full_research_preview_is_never_sent_or_trade_qualified(self):
        result = self.example()
        self.assertEqual(result["route"], "RESEARCH_ONLY")
        for text in ("49.50 - 50.00", "47.50", "55.00", "2.00",
                     "340.20", "4.90 / 4.90", "NIET VERZONDEN",
                     "GEEN KOOP OF INSTAPSIGNAAL"):
            self.assertIn(text, result["body"])
        for flag in ("send_enabled", "topic_configured", "trade_ready",
                     "order_placement_enabled"):
            self.assertFalse(result[flag])

    def test_incomplete_inputs_do_not_produce_body(self):
        result = self.example(net_profit_eur=None)
        self.assertIsNone(result["body"])
        self.assertEqual(result["reason"], "INCOMPLETE_FINANCIAL_PREVIEW")

    def test_invalid_financial_threshold_does_not_produce_body(self):
        for change in ({"rr": "1.99"}, {"net_profit_eur": "149.99"},
                       {"invalidation": "50"}, {"buy_fee_eur": "-1"}):
            with self.subTest(change=change):
                self.assertIsNone(self.example(**change)["body"])

    def test_forged_rr_cannot_promote_inconsistent_levels(self):\n        result = self.example(rr="4")\n        self.assertIsNone(result["body"])\n        self.assertEqual(result["reason"], "RR_NOT_CONSISTENT_WITH_ENTRY_ZONE")\n\n    def test_upper_entry_boundary_must_still_meet_two_r(self):\n        result = self.example(entry_high="51", rr="2")\n        self.assertIsNone(result["body"])\n        self.assertEqual(result["reason"], "RR_NOT_CONSISTENT_WITH_ENTRY_ZONE")\n\n    def test_unknown_phase_does_not_produce_body(self):
        result = build_offline_ntfy_preview("DEMO", "TRADE", entry_low="50")
        self.assertEqual(result["route"], "NONE")
        self.assertIsNone(result["body"])


if __name__ == "__main__":
    unittest.main()
