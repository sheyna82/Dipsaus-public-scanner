import unittest
from research_spoor3_input_audit import audit_us_recovery_report as audit

class Spoor3InputAuditTests(unittest.TestCase):
    def test_existing_pilot_fields_do_not_fabricate_score(self):
        r = audit({"candidates": [{"symbol": "EXAMPLE", "last_close_usd": 20,
                                   "signal_count": 6, "research_triage": {"sector_status": "UNVERIFIED"}}]})
        self.assertEqual(r["candidate_count"], 1)
        self.assertEqual(r["complete_count"], 0)
        self.assertEqual(len(r["candidates"][0]["missing_score_fields"]), 5)
        self.assertEqual(len(r["candidates"][0]["missing_risk_fields"]), 6)
        self.assertFalse(r["order_placement_enabled"])

    def test_empty_report_is_valid_not_ranked(self):
        r = audit({"candidates": []})
        self.assertEqual(r["status"], "INPUT_COVERAGE_AUDIT_ONLY")
        self.assertEqual(r["candidate_count"], 0)

    def test_malformed_report_fails_closed(self):
        self.assertEqual(audit({"candidates": None})["status"], "AUDIT_INPUT_BLOCKED")

    def test_bad_candidate_fails_closed(self):
        self.assertEqual(audit({"candidates": [None]})["status"], "AUDIT_INPUT_BLOCKED")

    def test_oversized_integer_is_invalid_not_exception(self):
        item = {"symbol": "EXAMPLE", "net_profit_eur": 10**1000}
        r = audit({"candidates": [item]})
        self.assertEqual(r["candidates"][0]["invalid_score_fields"], ["net_profit_eur"])
        self.assertFalse(r["candidates"][0]["ready_for_research_review"])

    def test_complete_input_is_not_trade_authorization(self):
        item = dict(symbol="EXAMPLE", net_profit_eur=180, net_rr=2.5,
                    relative_volume=1.5, market_context=0.8, sector_context=0.7,
                    risk_inputs=dict(bid=10, ask=10.01, average_daily_turnover_eur=2e6,
                                     relative_volume=1.5, sessions_until_earnings=12,
                                     earnings_calendar_checked=True))
        r = audit({"candidates": [item]})
        self.assertEqual(r["complete_count"], 1)
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])

if __name__ == "__main__":
    unittest.main()
