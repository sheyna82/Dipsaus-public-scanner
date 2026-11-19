"""Synthetic EUR broker evidence to net math: never trade-ready."""
import unittest
from datetime import datetime, timezone
from research_degiro_net_bridge import evaluate_degiro_research_scenario as evaluate

NOW = datetime(2026, 11, 19, 14, 15, tzinfo=timezone.utc)
BROKER = dict(isin="DE0006231004", operating_mic="XETR",
              instrument_currency="EUR", fee_currency="EUR",
              quote_source="DEGIRO", fee_source="DEGIRO", route_source="DEGIRO",
              quote_observed_utc="2026-11-19T14:14:30Z",
              fee_observed_utc="2026-11-19T14:00:00Z",
              route_observed_utc="2026-11-19T14:00:00Z",
              quote_bid=64.99, quote_ask=65,
              fee_buy_eur=4.9, fee_sell_eur=4.9,
              route_instrument_isin="DE0006231004", route_operating_mic="XETR")
TECH = dict(invalidation=64, target=70,
            buy_slippage_per_share=0, sell_slippage_per_share=0)

class DegiroNetBridgeTests(unittest.TestCase):
    def test_profitable_synthetic_scenario_stays_unauthenticated(self):
        r = evaluate(BROKER, TECH, now=NOW)
        self.assertEqual(r["status"], "UNAUTHENTICATED_RESEARCH_SCENARIO")
        self.assertGreater(r["net_profit_eur"], 150)
        self.assertGreaterEqual(r["net_rr"], 2)
        self.assertFalse(r["checks"]["evidence_verified"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])
    def test_wrong_route_blocks_before_math(self):
        r = evaluate({**BROKER, "route_operating_mic": "XAMS"}, TECH, now=NOW)
        self.assertEqual(r["status"], "BROKER_EVIDENCE_BLOCKED")
        self.assertNotIn("net_profit_eur", r)
    def test_stale_quote_blocks_before_math(self):
        r = evaluate({**BROKER, "quote_observed_utc": "2026-11-19T14:00:00Z"}, TECH, now=NOW)
        self.assertEqual(r["status"], "BROKER_EVIDENCE_BLOCKED")
    def test_public_provider_blocks_before_math(self):
        r = evaluate({**BROKER, "quote_source": "PUBLIC_PROVIDER"}, TECH, now=NOW)
        self.assertEqual(r["status"], "BROKER_EVIDENCE_BLOCKED")
    def test_missing_levels_blocks(self):
        self.assertEqual(evaluate(BROKER, {}, now=NOW)["status"], "TECHNICAL_EVIDENCE_BLOCKED")
    def test_unprofitable_scenario_still_blocked(self):
        r = evaluate(BROKER, {**TECH, "target": 65.5}, now=NOW)
        self.assertFalse(r["trade_ready"])
        self.assertEqual(r["status"], "RESEARCH_ONLY_BLOCKED")

    def test_missing_fee_timestamp_blocks_before_math(self):
        e = dict(BROKER)
        del e["fee_observed_utc"]
        r = evaluate(e, TECH, now=NOW)
        self.assertEqual(r["status"], "BROKER_METADATA_BLOCKED")
        self.assertEqual(r["group"], "fees")
    def test_stale_route_timestamp_blocks_before_math(self):
        r = evaluate({**BROKER, "route_observed_utc": "2026-11-17T14:00:00Z"}, TECH, now=NOW)
        self.assertEqual(r["status"], "BROKER_METADATA_BLOCKED")
        self.assertEqual(r["group"], "route")
    def test_future_fee_timestamp_blocks_before_math(self):
        r = evaluate({**BROKER, "fee_observed_utc": "2026-11-19T14:16:00Z"}, TECH, now=NOW)
        self.assertEqual(r["status"], "BROKER_METADATA_BLOCKED")
    def test_naive_route_timestamp_blocks_before_math(self):
        r = evaluate({**BROKER, "route_observed_utc": "2026-11-19T14:00:00"}, TECH, now=NOW)
        self.assertEqual(r["status"], "BROKER_METADATA_BLOCKED")

    def test_usd_instrument_cannot_be_assumed_eur(self):
        r = evaluate({**BROKER, "instrument_currency": "USD"}, TECH, now=NOW)
        self.assertEqual(r["status"], "CURRENCY_BLOCKED")
        self.assertNotIn("net_profit_eur", r)
    def test_unknown_fee_currency_blocks(self):
        r = evaluate({**BROKER, "fee_currency": None}, TECH, now=NOW)
        self.assertEqual(r["status"], "CURRENCY_BLOCKED")
    def test_missing_instrument_currency_blocks(self):
        e = dict(BROKER)
        del e["instrument_currency"]
        self.assertEqual(evaluate(e, TECH, now=NOW)["status"], "CURRENCY_BLOCKED")

if __name__ == "__main__":
    unittest.main()
