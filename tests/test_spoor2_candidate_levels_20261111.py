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

    def test_whole_shares_and_costs(self):
        result = module.money_scenario(
            budget_eur=3500, ask_usd=52.05, exit_bid_usd=58.15,
            invalidation_usd=49, eur_per_usd=0.92, buy_fee_eur=2,
            sell_fee_eur=2, buy_fx_rate=0.0025, sell_fx_rate=0.0025)
        self.assertLessEqual(result["purchase_eur"], 3500)
        self.assertGreater(result["net_profit_eur"], 0)
        self.assertEqual(result["reference_rr"], 2.0)
        self.assertFalse(result["trade_ready"])

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
