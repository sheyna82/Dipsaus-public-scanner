"""Offline regression checks for the isolated net scenario module."""
import unittest
from research_net_scenario import evaluate_net_scenario as calc


class NetScenarioTests(unittest.TestCase):
    def test_asm_gross_rr_two_fails_net(self):
        r = calc(ask=698, bid=697.8, invalidation=672, target=750,
                 budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9)
        self.assertEqual(r["shares"], 4)  # fees must fit the tranche
        self.assertFalse(r["checks"]["net_rr_at_least_2"])
        self.assertFalse(r["trade_ready"])

    def test_missing_fee_fails_closed(self):
        r = calc(ask=65, bid=64.99, invalidation=64, target=70,
                 budget_eur=3500, buy_fee_eur=None, sell_fee_eur=4.9)
        self.assertEqual(r["status"], "INVALID_OR_MISSING_INPUT")

    def test_qualifying_still_needs_human_review(self):
        r = calc(ask=65, bid=64.99, invalidation=64, target=70,
                 budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9,
                 evidence_verified=True)
        self.assertEqual(r["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])

    def test_unverified_never_qualifies(self):
        r = calc(ask=65, bid=64.99, invalidation=64, target=70,
                 budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9)
        self.assertEqual(r["status"], "RESEARCH_ONLY_BLOCKED")

    def test_spread_and_structure(self):
        r = calc(ask=65, bid=65.1, invalidation=64, target=70,
                 budget_eur=3500, buy_fee_eur=0, sell_fee_eur=0)
        self.assertEqual(r["status"], "STRUCTURE_BLOCKED")

    def test_slippage_can_block(self):
        r = calc(ask=65, bid=64.99, invalidation=64, target=66,
                 budget_eur=3500, buy_fee_eur=0, sell_fee_eur=0,
                 buy_slippage_per_share=1, sell_slippage_per_share=1)
        self.assertEqual(r["status"], "FRICTION_BLOCKED")

    def test_boolean_not_a_price(self):
        r = calc(ask=True, bid=1, invalidation=.5, target=2,
                 budget_eur=3500, buy_fee_eur=0, sell_fee_eur=0)
        self.assertEqual(r["status"], "INVALID_OR_MISSING_INPUT")


if __name__ == "__main__":
    unittest.main()
