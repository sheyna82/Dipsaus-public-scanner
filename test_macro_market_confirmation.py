import unittest
from datetime import datetime, timezone, timedelta
from macro_market_confirmation import assess_macro_market

class MarketConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 19, 14, tzinfo=timezone.utc)
        self.context = {"status":"HEADLINE_REVIEW_ONLY","headlines":[{"headline":"tariff"}]}
    def test_positive_requires_two_fresh_indexes(self):
        quotes={t:{"timestamp_utc":self.now.isoformat(),"change_pct":1.2} for t in ("SPY","QQQ")}
        r=assess_macro_market(self.context,quotes,self.now)
        self.assertEqual(r["status"],"BROAD_MARKET_POSITIVE_RESEARCH")
        self.assertFalse(r["notify"])
        self.assertFalse(r["trade_ready"])
    def test_stale_or_missing_is_not_confirmation(self):
        quotes={"SPY":{"timestamp_utc":self.now.isoformat(),"change_pct":2},
                "QQQ":{"timestamp_utc":(self.now-timedelta(hours=1)).isoformat(),"change_pct":2}}
        self.assertEqual(assess_macro_market(self.context,quotes,self.now)["status"],"INSUFFICIENT_MARKET_CONFIRMATION")
    def test_no_news_no_confirmation(self):
        quotes={t:{"timestamp_utc":self.now.isoformat(),"change_pct":1} for t in ("SPY","QQQ")}
        self.assertEqual(assess_macro_market({},quotes,self.now)["status"],"INSUFFICIENT_MARKET_CONFIRMATION")
