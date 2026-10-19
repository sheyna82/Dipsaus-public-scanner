import unittest
from datetime import datetime, timezone, timedelta
from macro_risk_watch import evaluate_risk

class MacroRiskTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 19, 14, tzinfo=timezone.utc)
        self.context = {"status":"HEADLINE_REVIEW_ONLY",
                        "headlines":[{"headline":"Military strike escalates conflict"}]}
    def quotes(self):
        return {s:{"timestamp_utc":self.now.isoformat(),"change_pct":v}
                for s,v in {"SPY":-1.1,"QQQ":-1.5,"VIXY":2.3,"XLE":0.9,"ITA":0.4}.items()}
    def test_risk_off_silent_and_sector_divergence(self):
        r=evaluate_risk(self.context,self.quotes(),self.now)
        self.assertEqual(r["status"],"RISK_OFF_RESEARCH")
        self.assertTrue(r["broad_selloff"])
        self.assertTrue(r["volatility_proxy_rising"])
        self.assertTrue(r["sector_divergence"])
        self.assertFalse(r["notify"])
        self.assertFalse(r["trade_ready"])
    def test_stale_market_data_fails_closed(self):
        q=self.quotes()
        q["QQQ"]["timestamp_utc"]=(self.now-timedelta(hours=1)).isoformat()
        self.assertEqual(evaluate_risk(self.context,q,self.now)["status"],"INDEX_DATA_MISSING")
    def test_no_risk_headline(self):
        self.assertEqual(evaluate_risk({"status":"HEADLINE_REVIEW_ONLY","headlines":[]},self.quotes(),self.now)["status"],"NO_VERIFIED_RISK_CONTEXT")
