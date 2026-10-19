"""Unit tests for the isolated, research-only risk plan."""
import unittest
from risk_budget_plan import build_trade_plan, RISK_BUDGETS_EUR


class RiskBudgetPlanTests(unittest.TestCase):
    def test_standard_sizing(self):
        p = build_trade_plan(100, 97, 109, verified=True)
        self.assertEqual(p.shares, 25)
        self.assertEqual(p.planned_loss, 75)
        self.assertEqual(p.potential_profit, 225)
        self.assertTrue(p.eligible)

    def test_capital_limit(self):
        p = build_trade_plan(10, 9.9, 12, verified=True)
        self.assertEqual(p.shares, 350)
        self.assertLessEqual(p.investment, 3500)

    def test_cautious_risk(self):
        p = build_trade_plan(100, 96, 116, risk_budget_eur=RISK_BUDGETS_EUR["cautious"], verified=True)
        self.assertEqual(p.shares, 12)
        self.assertLessEqual(p.planned_loss, 50)

    def test_unverified_cannot_be_eligible(self):
        p = build_trade_plan(100, 97, 109)
        self.assertFalse(p.eligible)
        self.assertIn("BROKER_AND_SETUP_VERIFICATION_REQUIRED", p.blockers)

    def test_profit_and_rr_gates(self):
        p = build_trade_plan(100, 97, 104, verified=True)
        self.assertFalse(p.eligible)
        self.assertIn("REWARD_RISK_BELOW_MINIMUM", p.blockers)
        self.assertIn("GROSS_PROFIT_BELOW_MINIMUM", p.blockers)

    def test_rejects_invalid_levels(self):
        for levels in ((100, 100, 110), (100, 101, 110), (100, 97, 96)):
            with self.assertRaises(ValueError):
                build_trade_plan(*levels)


if __name__ == "__main__":
    unittest.main()
