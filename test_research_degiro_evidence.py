"""Offline negative tests for untrusted broker source assertions."""
import unittest
from datetime import datetime, timezone, timedelta
from research_degiro_evidence import inspect_degiro_evidence

NOW = datetime(2026, 11, 19, 14, 15, tzinfo=timezone.utc)
GOOD = dict(isin="DE0006231004", operating_mic="XETR", quote_source="DEGIRO",
            fee_source="DEGIRO", route_source="DEGIRO",
            quote_observed_utc="2026-11-19T14:14:30Z", quote_bid=30.0,
            quote_ask=30.1, fee_buy_eur=4.9, fee_sell_eur=4.9,
            route_instrument_isin="DE0006231004", route_operating_mic="XETR")

class DegiroEvidenceTests(unittest.TestCase):
    def check(self, **changes):
        return inspect_degiro_evidence({**GOOD, **changes}, now=NOW)
    def test_consistent_claims_never_authorize_trade(self):
        result = self.check()
        self.assertEqual(result["status"], "DEGIRO_CLAIMS_STRUCTURALLY_CONSISTENT")
        for field in ("trade_ready", "order_placement_enabled", "broker_route_verified",
                      "degiro_fee_verified", "source_authenticity_independently_verified"):
            self.assertFalse(result[field])
    def test_public_quote_masquerading_blocked(self):
        self.assertEqual(self.check(quote_source="YAHOO")["reason"], "NON_BROKER_SOURCE")
    def test_public_fee_masquerading_blocked(self):
        self.assertEqual(self.check(fee_source="PUBLIC")["reason"], "NON_BROKER_SOURCE")
    def test_route_mismatch_blocked(self):
        self.assertEqual(self.check(route_operating_mic="XAMS")["reason"], "ROUTE_IDENTITY_MISMATCH")
    def test_wrong_isin_blocked(self):
        self.assertEqual(self.check(route_instrument_isin="NL0010273215")["reason"], "ROUTE_IDENTITY_MISMATCH")
    def test_stale_quote_blocked(self):
        self.assertEqual(self.check(quote_observed_utc="2026-11-19T14:12:00Z")["reason"], "STALE_OR_FUTURE_QUOTE")
    def test_future_quote_blocked(self):
        self.assertEqual(self.check(quote_observed_utc="2026-11-19T14:16:00Z")["reason"], "STALE_OR_FUTURE_QUOTE")
    def test_crossed_market_blocked(self):
        self.assertEqual(self.check(quote_bid=31.0)["reason"], "INVALID_MARKET_VALUES")
    def test_negative_fee_blocked(self):
        self.assertEqual(self.check(fee_sell_eur=-1)["reason"], "INVALID_MARKET_VALUES")
    def test_nonfinite_quote_blocked(self):
        self.assertEqual(self.check(quote_ask=float("nan"))["reason"], "INVALID_NUMERIC_EVIDENCE")
    def test_missing_field_blocked(self):
        e = dict(GOOD)
        del e["fee_source"]
        self.assertEqual(inspect_degiro_evidence(e, now=NOW)["reason"], "MISSING_FIELDS")

if __name__ == "__main__":
    unittest.main()
