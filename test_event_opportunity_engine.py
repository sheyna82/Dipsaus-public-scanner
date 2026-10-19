"""Offline regression tests for conservative event research."""
import unittest
from datetime import date
from event_opportunity_engine import classify_event_opportunities,event_research_text

class OpportunityTests(unittest.TestCase):
    def test_pre_event(self):
        x=classify_event_opportunities("2026-10-29",date(2026,10,20))
        self.assertEqual([r["stage"] for r in x],["PRE_EVENT_RUN_UP"])
        self.assertFalse(x[0]["eligible"])
    def test_event_hold_requires_data_even_when_complete(self):
        day=date(2026,10,29)
        missing=classify_event_opportunities("2026-10-29",day)[0]
        self.assertIn("Insufficient evidence",missing["reason"])
        full=dict.fromkeys(("issuer_confirmed_date","fresh_quote","implied_move_pct","historical_event_moves","consensus_and_guidance","downside_gap_stress_pct","upside_scenario_pct"),1)
        result=classify_event_opportunities("2026-10-29",day,full)
        self.assertTrue(all(not x["eligible"] for x in result))
        self.assertIn("stop-loss",result[0]["reason"])
    def test_post_event_and_no_chase(self):
        x=classify_event_opportunities("2026-10-21",date(2026,10,22))
        self.assertEqual(x[0]["stage"],"POST_EVENT_RECOVERY")
        self.assertIn("Do not chase",x[0]["event_risk"])
    def test_outside_window(self):
        self.assertIsNone(event_research_text("AMZN","2026-10-29",date(2026,11,10)))
    def test_no_trade_ready(self):
        for offset in (-2,0,2,5):
            x=classify_event_opportunities("2026-10-29",date(2026,10,29)+__import__("datetime").timedelta(days=offset))
            self.assertTrue(all(not r["eligible"] for r in x))
if __name__=="__main__":unittest.main()
