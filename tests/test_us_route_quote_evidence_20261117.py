import unittest
from datetime import datetime, timezone, timedelta
from research.us_route_quote_evidence_20261117 import review_us_route_quote

NOW = datetime(2026, 11, 17, 16, 0, tzinfo=timezone.utc)

def sample():
    route = {"symbol": "TEST", "generated_utc": (NOW-timedelta(minutes=2)).isoformat(),
             "last_bar_date": "2026-11-17", "break_above_usd": 20.0,
             "hold_zone_usd": [19.9,20.1], "phone_notification_eligible": True}
    quote = {"symbol": "TEST", "provider_quote_utc": (NOW-timedelta(seconds=30)).isoformat(),
             "provider_quote": 20.0, "provider_freshness_pass": True,
             "intraday_hold_confirmed": True}
    return route, quote

class RouteQuoteEvidenceTests(unittest.TestCase):
    def check(self, route, quote):
        return review_us_route_quote(route, quote, now=NOW)

    def test_fresh_consistent_still_blocked(self):
        route, quote = sample()
        r = self.check(route, quote)
        self.assertTrue(r["route_quote_temporally_consistent"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["notify"])
        self.assertIn("NET_PROFIT_AND_RR_UNVERIFIED", r["blocks"])

    def test_stale_route(self):
        route, quote = sample()
        route["generated_utc"] = (NOW-timedelta(hours=1)).isoformat()
        self.assertIn("ROUTE_STALE_OR_FUTURE", self.check(route,quote)["blocks"])

    def test_stale_quote(self):
        route, quote = sample()
        quote["provider_quote_utc"] = (NOW-timedelta(minutes=5)).isoformat()
        self.assertIn("QUOTE_STALE_OR_FUTURE", self.check(route,quote)["blocks"])

    def test_symbol_mismatch(self):
        route, quote = sample()
        quote["symbol"] = "OTHER"
        self.assertIn("SYMBOL_MISMATCH_OR_UNRESOLVED", self.check(route,quote)["blocks"])

    def test_session_mismatch(self):
        route, quote = sample()
        route["last_bar_date"] = "2026-11-16"
        self.assertIn("ROUTE_BAR_SESSION_MISMATCH", self.check(route,quote)["blocks"])

    def test_malformed_levels(self):
        route, quote = sample()
        route["hold_zone_usd"] = [20.1,19.9]
        self.assertIn("ROUTE_LEVELS_INVALID", self.check(route,quote)["blocks"])

    def test_missing_timestamp(self):
        route, quote = sample()
        route.pop("generated_utc")
        self.assertIn("ROUTE_TIME_UNRESOLVED", self.check(route,quote)["blocks"])

    def test_quote_predates_route(self):
        route, quote = sample()
        route["generated_utc"] = (NOW-timedelta(seconds=5)).isoformat()
        self.assertIn("QUOTE_PREDATES_ROUTE", self.check(route,quote)["blocks"])

if __name__ == "__main__":
    unittest.main()
