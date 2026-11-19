"""Offline regression checks for the isolated net scenario module."""
import unittest
from research_net_scenario import evaluate_net_scenario as calc


class NetScenarioTests(unittest.TestCase):
    def test_asm_gross_rr_two_fails_net(self):
        r = calc(ask=698, bid=697.8, invalidation=672, target=750,
                 budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9)
        self.assertEqual(r["shares"], 5)  # 5*698 + 4.90 = 3494.90
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


    def test_fx_friction_reduces_share_count(self):
        base = calc(ask=698, bid=697.8, invalidation=672, target=750,
                    budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9)
        fx = calc(ask=698, bid=697.8, invalidation=672, target=750,
                  budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9,
                  fx_buy_fee_rate=.0025, fx_sell_fee_rate=.0025)
        self.assertEqual(base["shares"], 5)
        self.assertEqual(fx["shares"], 4)
        self.assertLess(fx["net_profit_eur"], base["net_profit_eur"])

    def test_negative_fx_fee_rejected(self):
        r = calc(ask=65, bid=64.99, invalidation=64, target=70,
                 budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9,
                 fx_buy_fee_rate=-.01)
        self.assertEqual(r["status"], "INVALID_OR_MISSING_INPUT")

    def test_fx_friction_can_turn_profit_negative(self):
        r = calc(ask=65, bid=64.99, invalidation=64, target=65.5,
                 budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9,
                 fx_buy_fee_rate=.01, fx_sell_fee_rate=.01)
        self.assertLess(r["net_profit_eur"], 0)
        self.assertFalse(r["checks"]["net_profit_at_least_150_eur"])


    def test_gle_snapshot_net_threshold_not_met(self):
        # Illustrative 19 Nov broker snapshot; invalidation/target not verified.
        r = calc(ask=64.95, bid=64.94, invalidation=64.52, target=67.61,
                 budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9)
        self.assertEqual(r["shares"], 53)
        self.assertFalse(r["checks"]["net_profit_at_least_150_eur"])
        self.assertFalse(r["trade_ready"])

    def test_asml_snapshot_target_is_hypothetical(self):
        r = calc(ask=1311.60, bid=1311.40, invalidation=1293.60,
                 target=1400, budget_eur=3500,
                 buy_fee_eur=4.9, sell_fee_eur=4.9)
        self.assertEqual(r["shares"], 2)
        self.assertGreater(r["net_profit_eur"], 150)
        self.assertEqual(r["status"], "RESEARCH_ONLY_BLOCKED")

    def test_nokia_snapshot_rr_below_two(self):
        # Snapshot is delayed; no verified entry signal.
        r = calc(ask=7.116, bid=7.112, invalidation=6.85, target=7.50,
                 budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9)
        self.assertFalse(r["checks"]["net_rr_at_least_2"])
        self.assertFalse(r["trade_ready"])

    def test_fx_zero_is_valid_for_eur_instrument(self):
        r = calc(ask=65, bid=64.99, invalidation=64, target=70,
                 budget_eur=3500, buy_fee_eur=4.9, sell_fee_eur=4.9,
                 fx_buy_fee_rate=0, fx_sell_fee_rate=0)
        self.assertEqual(r["shares"], 53)

    def test_budget_exhausted_by_fee(self):
        r = calc(ask=65, bid=64.99, invalidation=64, target=70,
                 budget_eur=3500, buy_fee_eur=3500, sell_fee_eur=4.9)
        self.assertEqual(r["status"], "BUDGET_BLOCKED")


if __name__ == "__main__":
    unittest.main()
