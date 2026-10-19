import unittest
from trade_lifecycle import portfolio_risk, profit_protection, pretrade_gate


class LifecycleTests(unittest.TestCase):
    def test_ordinary_pullback_not_forced_exit(self):
        p = profit_protection(entry=100, current=110, peak=112, shares=10,
                              fresh_data=True, broker_verified=True)
        self.assertEqual(p["level"], "HOLD_REVIEW")
        self.assertFalse(p["automatic_order"])

    def test_profit_giveback_escalation(self):
        p = profit_protection(entry=100, current=104, peak=120, shares=10,
                              fresh_data=True, broker_verified=True)
        self.assertEqual(p["level"], "URGENT_EXIT_REVIEW")
        self.assertEqual(p["given_back_gross_eur"], 160)

    def test_trend_break_escalates(self):
        p = profit_protection(entry=100, current=102, peak=103, shares=10,
                              confirmed_trend_break=True)
        self.assertEqual(p["level"], "URGENT_EXIT_REVIEW")
        self.assertFalse(p["ready_for_broker_action"])

    def test_portfolio_risk_aggregation(self):
        p = portfolio_risk([{"planned_risk_eur": 75, "sector": "energy"},
                            {"planned_risk_eur": 100, "sector": "energy"}])
        self.assertIn("SECTOR_RISK_LIMIT", p["blockers"])

    def test_pretrade_gate_never_blocks_discovery(self):
        p = pretrade_gate(technical_setup_verified=False, broker_quote_verified=False,
                          event_risk_reviewed=False, fx_verified=False,
                          spread_acceptable=False, stop_order_supported=False,
                          existing_positions=[], proposed_risk_eur=75,
                          proposed_sector="industry")
        self.assertFalse(p["execution_ready"])
        self.assertTrue(p["discovery_alert_allowed"])

    def test_pretrade_gate_ready_with_verified_inputs(self):
        p = pretrade_gate(technical_setup_verified=True, broker_quote_verified=True,
                          event_risk_reviewed=True, fx_verified=True,
                          spread_acceptable=True, stop_order_supported=True,
                          existing_positions=[], proposed_risk_eur=75,
                          proposed_sector="industry")
        self.assertTrue(p["execution_ready"])

    def test_invalid_peak(self):
        with self.assertRaises(ValueError):
            profit_protection(entry=100, current=110, peak=105, shares=10)


if __name__ == "__main__":
    unittest.main()
