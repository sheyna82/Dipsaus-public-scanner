import unittest
from decimal import Decimal
from research.spoor2_eu_money_scenario_20261111 import european_money_scenario

def fixture(**overrides):
    args = dict(quote_unit="GBp", ask="125.5", target_bid="145",
                invalidation="120", budget_eur="3500", eur_per_base_unit="1.2",
                buy_fee_eur="3", sell_fee_eur="3", buy_fx_rate="0.0025",
                sell_fx_rate="0.0025", buy_slippage="0.002",
                sell_slippage="0.002")
    args.update(overrides)
    return european_money_scenario(**args)

class EuropeanMoneyScenarioTests(unittest.TestCase):
    def test_gbp_pence_scenario_stays_research_only(self):
        r = fixture()
        self.assertEqual(r["status"], "ILLUSTRATIVE_NOT_VERIFIED")
        self.assertEqual(r["base_currency"], "GBP")
        self.assertGreater(r["whole_shares"], 0)
        self.assertFalse(r["trade_ready"])
        self.assertIn("FX_EXTERNAL_ATTESTATION_NOT_CONNECTED", r["blocks"])

    def test_budget_never_exceeded(self):
        r = fixture()
        self.assertLessEqual(Decimal(r["purchase_eur"]), Decimal("3500"))

    def test_slippage_reduces_profit(self):
        self.assertLess(Decimal(fixture()["net_profit_eur"]),
                        Decimal(fixture(buy_slippage="0", sell_slippage="0")["net_profit_eur"]))

    def test_gbp_vs_gbp_pence_consistent(self):
        a = fixture()
        b = fixture(quote_unit="GBP", ask="1.255", target_bid="1.45",
                    invalidation="1.20")
        self.assertEqual(a["net_profit_eur"], b["net_profit_eur"])

    def test_bad_quote_unit_blocks(self):
        self.assertEqual(fixture(quote_unit="gbp")["status"], "BLOCKED")

    def test_nonfinite_and_boolean_inputs_block(self):
        for v in ("NaN", "Infinity", True, "-1"):
            self.assertEqual(fixture(eur_per_base_unit=v)["status"], "BLOCKED")

    def test_inverted_levels_block(self):
        self.assertEqual(fixture(invalidation="130")["status"], "BLOCKED")

    def test_insufficient_budget_blocks(self):
        self.assertIn("BUDGET_INSUFFICIENT", fixture(budget_eur="1")["blocks"])

    def test_fx_rate_over_one_blocks(self):
        self.assertIn("FX_FRICTION_INVALID", fixture(buy_fx_rate="1")["blocks"])

if __name__ == "__main__":
    unittest.main()
