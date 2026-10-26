"""Deterministic historical-scenario replay; synthetic prices, NOT market backtest."""
import unittest
from risk_budget_plan import build_trade_plan
from trade_lifecycle import profit_protection, pretrade_gate


class ScenarioReplay(unittest.TestCase):
    def test_fer_like_loss_is_budgeted(self):
        # Illustrative only; these are not FER historical prices.
        p = build_trade_plan(44, 43, 47, verified=True)
        self.assertTrue(p.eligible)
        self.assertEqual(p.shares, 75)
        self.assertEqual(p.planned_loss, 75)
        self.assertEqual(p.potential_profit, 225)

    def test_early_entry_signal_survives_missing_execution_data(self):
        gate = pretrade_gate(technical_setup_verified=False,
                             broker_quote_verified=False, event_risk_reviewed=False,
                             fx_verified=False, spread_acceptable=False,
                             stop_order_supported=False, existing_positions=[],
                             proposed_risk_eur=75, proposed_sector="industrial")
        self.assertTrue(gate["discovery_alert_allowed"])
        self.assertFalse(gate["execution_ready"])

    def test_profit_peak_then_deterioration(self):
        hold = profit_protection(entry=50, current=59, peak=60, shares=50,
                                 fresh_data=True, broker_verified=True)
        warning = profit_protection(entry=50, current=56, peak=60, shares=50,
                                    fresh_data=True, broker_verified=True)
        urgent = profit_protection(entry=50, current=53, peak=60, shares=50,
                                   confirmed_trend_break=True,
                                   fresh_data=True, broker_verified=True)
        self.assertEqual(hold["level"], "HOLD_REVIEW")
        self.assertEqual(warning["level"], "PROTECT_PROFIT_REVIEW")
        self.assertEqual(urgent["level"], "URGENT_EXIT_REVIEW")

    def test_gap_risk_is_not_guaranteed(self):
        p = build_trade_plan(100, 97, 109, verified=True)
        self.assertEqual(p.planned_loss, 75)
        # A gap to 90 would lose 250 EUR on 25 shares, before fees.
        self.assertEqual((100 - 90) * p.shares, 250)


if __name__ == "__main__":
    unittest.main()
