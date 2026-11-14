"""Regression checks for isolated Spoor 2 calculations; no live imports."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "research" / "spoor2_candidate_levels_20261111.py"
spec = importlib.util.spec_from_file_location("spoor2_levels", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Spoor2ResearchTests(unittest.TestCase):
    def test_unknown_never_approves(self):
        self.assertFalse(module.research_levels({}, 0)["trade_ready"])
        self.assertFalse(module.research_levels({}, 50)["trade_ready"])

    def test_historical_references_never_verified(self):
        data = {"recent_10d_low_invalidation_reference_usd": 49,
                "historical_overhead_pivot_zones": [
                    {"low_usd": 54}, {"low_usd": 58}, {"low_usd": 51}]}
        result = module.research_levels(data, 52)
        self.assertEqual(result["required_2r_target_usd"], 58)
        self.assertEqual(result["resistance_references_usd"], [54.0, 58.0])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["resistance_verified"])

    def test_historical_levels_use_nearest_overhead_resistance(self):
        data={"recent_10d_low_invalidation_reference_usd":49,
              "historical_overhead_pivot_zones":[{"low_usd":60},{"low_usd":54}]}
        r=module.research_levels(data,52)
        self.assertEqual(r["resistance_references_usd"],[54.0,60.0])
        self.assertEqual(r["entry_zone_research"]["status"],
                         "REFERENCE_RR_BELOW_MINIMUM")
        self.assertNotIn("entry_zone_reference_usd",r["entry_zone_research"])
        self.assertFalse(r["trade_ready"])

    def test_historical_levels_without_invalidation_have_no_entry_zone(self):
        r=module.research_levels(
            {"historical_overhead_pivot_zones":[{"low_usd":60}]},52)
        self.assertIsNone(r["entry_zone_research"])
        self.assertFalse(r["trade_ready"])

    def test_entry_zone_ceiling_is_mathematically_two_r(self):
        r=module.research_entry_zone(
            broker_ask_usd=52, invalidation_reference_usd=49,
            resistance_reference_usd=60)
        self.assertEqual(r["status"],"ILLUSTRATIVE_ENTRY_ZONE_ONLY")
        self.assertAlmostEqual(r["entry_ceiling_reference_usd"],(60+2*49)/3)
        self.assertEqual(r["entry_zone_reference_usd"][0],52)
        self.assertFalse(r["entry_zone_verified"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])

    def test_entry_zone_blocks_when_reference_rr_too_low(self):
        r=module.research_entry_zone(
            broker_ask_usd=55, invalidation_reference_usd=49,
            resistance_reference_usd=60)
        self.assertEqual(r["status"],"REFERENCE_RR_BELOW_MINIMUM")
        self.assertNotIn("entry_zone_reference_usd",r)
        self.assertFalse(r["trade_ready"])

    def test_entry_zone_invalid_inputs_fail_closed(self):
        for ask,invalid,level,rr in ((52,52,60,2),(60,49,60,2),
                                     (52,49,60,1.5),(True,49,60,2),
                                     (float("nan"),49,60,2),
                                     (52,49,float("inf"),2)):
            with self.subTest(values=(ask,invalid,level,rr)):
                r=module.research_entry_zone(
                    broker_ask_usd=ask,invalidation_reference_usd=invalid,
                    resistance_reference_usd=level,minimum_rr=rr)
                self.assertEqual(r["status"],"UNKNOWN")
                self.assertFalse(r["trade_ready"])

    def test_whole_shares_and_costs(self):
        result = module.money_scenario(
            budget_eur=3500, ask_usd=52.05, exit_bid_usd=58.15,
            invalidation_usd=49, eur_per_usd=0.92, buy_fee_eur=2,
            sell_fee_eur=2, buy_fx_rate=0.0025, sell_fx_rate=0.0025)
        self.assertLessEqual(result["purchase_eur"], 3500)
        self.assertGreater(result["net_profit_eur"], 0)
        self.assertEqual(result["reference_rr"], 2.0)
        self.assertFalse(result["trade_ready"])

    def test_net_rr_accounts_for_round_trip_friction(self):
        base=dict(budget_eur=3500, ask_usd=52, exit_bid_usd=58,
                  invalidation_usd=49, eur_per_usd=0.92,
                  buy_fee_eur=0, sell_fee_eur=0,
                  buy_fx_rate=0, sell_fx_rate=0)
        zero=module.money_scenario(**base)
        friction=module.money_scenario(**{**base,"buy_fee_eur":3,
            "sell_fee_eur":3,"buy_fx_rate":0.0025,"sell_fx_rate":0.0025})
        self.assertAlmostEqual(zero["net_reference_rr_after_friction"],2.0)
        self.assertLess(friction["net_reference_rr_after_friction"],2)
        self.assertGreater(friction["net_downside_eur_at_invalidation"],0)
        self.assertFalse(friction["trade_ready"])

    def test_net_rr_changes_with_execution_slippage(self):
        base=dict(budget_eur=3500, ask_usd=52, exit_bid_usd=60,
                  invalidation_usd=49, eur_per_usd=0.92,
                  buy_fee_eur=2, sell_fee_eur=2,
                  buy_fx_rate=0.0025, sell_fx_rate=0.0025)
        normal=module.money_scenario(**base)
        slipped=module.money_scenario(**{**base,"slippage_buy_usd":0.2,
            "slippage_sell_usd":0.2})
        self.assertLess(slipped["net_reference_rr_after_friction"],
                        normal["net_reference_rr_after_friction"])
        self.assertFalse(slipped["trade_ready"])

    def test_invalidation_downside_includes_sell_slippage(self):
        base = dict(budget_eur=3500, ask_usd=52, exit_bid_usd=60,
                    invalidation_usd=49, eur_per_usd=1,
                    buy_fee_eur=0, sell_fee_eur=0,
                    buy_fx_rate=0, sell_fx_rate=0)
        normal = module.money_scenario(**base)
        slipped = module.money_scenario(**{**base, "slippage_sell_usd": 0.5})
        shares = normal["whole_shares"]
        self.assertEqual(slipped["whole_shares"], shares)
        self.assertAlmostEqual(
            slipped["net_downside_eur_at_invalidation"]
            - normal["net_downside_eur_at_invalidation"], shares * 0.5, places=2)
        self.assertLess(slipped["net_reference_rr_after_friction"],
                        normal["net_reference_rr_after_friction"])
        self.assertFalse(slipped["trade_ready"])

    def test_slippage_exceeding_invalidation_reference_fails_closed(self):
        row = module.money_scenario(
            budget_eur=3500, ask_usd=52, exit_bid_usd=60,
            invalidation_usd=49, eur_per_usd=0.92,
            buy_fee_eur=2, sell_fee_eur=2,
            buy_fx_rate=0.0025, sell_fx_rate=0.0025,
            slippage_sell_usd=49)
        self.assertEqual(row["status"], "UNKNOWN")
        self.assertFalse(row["trade_ready"])

    def test_bad_inputs_fail_closed(self):
        common = dict(budget_eur=3500, ask_usd=52, exit_bid_usd=60,
                      invalidation_usd=49, eur_per_usd=0.92,
                      buy_fee_eur=2, sell_fee_eur=2, buy_fx_rate=0.0025,
                      sell_fx_rate=0.0025)
        for bad in (float("nan"), -1, True):
            self.assertFalse(module.money_scenario(**dict(common, ask_usd=bad))["trade_ready"])
        self.assertFalse(module.money_scenario(**dict(common, invalidation_usd=53))["trade_ready"])


if __name__ == "__main__":
    unittest.main()
