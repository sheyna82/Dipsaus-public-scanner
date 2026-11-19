"""Offline bridge tests; no broker connectivity or trading."""
import unittest
from research_net_bridge import evaluate_verified_research_evidence as bridge


class NetBridgeTests(unittest.TestCase):
    def setUp(self):
        self.evidence = {
            "broker_ask": 65, "broker_bid": 64.99,
            "invalidation": 64, "target": 70,
            "buy_fee_eur": 4.9, "sell_fee_eur": 4.9,
            "fx_eur_per_unit": 1, "fx_buy_fee_rate": 0,
            "fx_sell_fee_rate": 0, "broker_quote_verified": True,
            "levels_verified": True, "fees_verified": True,
            "fx_verified": True, "quote_freshness_verified": True}

    def test_eu_verified_still_non_executable(self):
        r = bridge(self.evidence, market="EU")
        self.assertEqual(r["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(r["trade_ready"])

    def test_us_verified_still_non_executable(self):
        r = bridge(self.evidence, market="US")
        self.assertEqual(r["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(r["order_placement_enabled"])

    def test_missing_broker_quote_fails_closed(self):
        e = dict(self.evidence)
        e.pop("broker_ask")
        r = bridge(e, market="EU")
        self.assertEqual(r["status"], "DATA_BLOCKED")

    def test_stale_quote_fails_closed(self):
        e = dict(self.evidence, quote_freshness_verified=False)
        r = bridge(e, market="US")
        self.assertEqual(r["status"], "REVIEW_BLOCKED")

    def test_unknown_fee_fails_closed(self):
        e = dict(self.evidence, fx_buy_fee_rate=None)
        r = bridge(e, market="US")
        self.assertEqual(r["status"], "DATA_BLOCKED")

    def test_invalid_market_fails_closed(self):
        r = bridge(self.evidence, market="UNKNOWN")
        self.assertEqual(r["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
