"""Synthetic EUR broker evidence to net math: never trade-ready."""
import unittest
from datetime import datetime, timezone
from research_degiro_net_bridge import evaluate_degiro_research_scenario as evaluate

NOW = datetime(2026, 11, 19, 14, 15, tzinfo=timezone.utc)
BROKER = dict(isin="DE0006231004", operating_mic="XETR",
              instrument_currency="EUR", fee_currency="EUR",
              quote_instrument_isin="DE0006231004", quote_operating_mic="XETR",
              fee_instrument_isin="DE0006231004", fee_operating_mic="XETR",
              fee_route_instrument_isin="DE0006231004", fee_route_operating_mic="XETR",
              quote_source="DEGIRO", fee_source="DEGIRO", route_source="DEGIRO",
              quote_observed_utc="2026-11-19T14:14:30Z",
              fee_observed_utc="2026-11-19T14:00:00Z",
              route_observed_utc="2026-11-19T14:00:00Z",
              quote_bid=64.99, quote_ask=65,
              fee_buy_eur=4.9, fee_sell_eur=4.9,
              fee_evidence={"evidence_kind": "OFFICIAL_PUBLIC_SCHEDULE"},
              route_instrument_isin="DE0006231004", route_operating_mic="XETR")
TECH = dict(instrument_isin="DE0006231004", operating_mic="XETR",
            levels_observed_utc="2026-11-19T14:00:00Z",
            invalidation=64, target=70,
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

    def test_wrong_technical_isin_blocks(self):
        r = evaluate(BROKER, {**TECH, "instrument_isin": "NL0010273215"}, now=NOW)
        self.assertEqual(r["status"], "TECHNICAL_PROVENANCE_BLOCKED")
        self.assertEqual(r["reason"], "TECHNICAL_INSTRUMENT_MISMATCH")
    def test_wrong_technical_mic_blocks(self):
        r = evaluate(BROKER, {**TECH, "operating_mic": "XAMS"}, now=NOW)
        self.assertEqual(r["status"], "TECHNICAL_PROVENANCE_BLOCKED")
    def test_stale_technical_levels_block(self):
        r = evaluate(BROKER, {**TECH, "levels_observed_utc": "2026-11-17T14:00:00Z"}, now=NOW)
        self.assertEqual(r["status"], "TECHNICAL_PROVENANCE_BLOCKED")
    def test_naive_technical_timestamp_blocks(self):
        r = evaluate(BROKER, {**TECH, "levels_observed_utc": "2026-11-19T14:00:00"}, now=NOW)
        self.assertEqual(r["status"], "TECHNICAL_PROVENANCE_BLOCKED")
    def test_missing_technical_timestamp_blocks(self):
        t = dict(TECH)
        del t["levels_observed_utc"]
        self.assertEqual(evaluate(BROKER, t, now=NOW)["status"], "TECHNICAL_PROVENANCE_BLOCKED")
    def test_future_technical_levels_block(self):
        r = evaluate(BROKER, {**TECH, "levels_observed_utc": "2026-11-19T14:16:00Z"}, now=NOW)
        self.assertEqual(r["status"], "TECHNICAL_PROVENANCE_BLOCKED")

    def test_fee_from_different_instrument_blocks(self):
        r = evaluate({**BROKER, "fee_instrument_isin": "NL0010273215"}, TECH, now=NOW)
        self.assertEqual(r["status"], "FEE_ROUTE_BINDING_BLOCKED")
        self.assertNotIn("net_profit_eur", r)
    def test_fee_from_different_venue_blocks(self):
        r = evaluate({**BROKER, "fee_operating_mic": "XAMS"}, TECH, now=NOW)
        self.assertEqual(r["status"], "FEE_ROUTE_BINDING_BLOCKED")
    def test_fee_route_mismatch_blocks(self):
        r = evaluate({**BROKER, "fee_route_operating_mic": "XAMS"}, TECH, now=NOW)
        self.assertEqual(r["status"], "FEE_ROUTE_BINDING_BLOCKED")
    def test_missing_fee_instrument_binding_blocks(self):
        e = dict(BROKER)
        del e["fee_instrument_isin"]
        self.assertEqual(evaluate(e, TECH, now=NOW)["status"], "FEE_ROUTE_BINDING_BLOCKED")

    def test_quote_from_other_instrument_blocks(self):
        r = evaluate({**BROKER, "quote_instrument_isin": "NL0010273215"}, TECH, now=NOW)
        self.assertEqual(r["status"], "QUOTE_IDENTITY_BLOCKED")
        self.assertNotIn("net_profit_eur", r)
    def test_quote_from_other_venue_blocks(self):
        r = evaluate({**BROKER, "quote_operating_mic": "XAMS"}, TECH, now=NOW)
        self.assertEqual(r["status"], "QUOTE_IDENTITY_BLOCKED")
    def test_missing_quote_binding_blocks(self):
        e = dict(BROKER)
        del e["quote_instrument_isin"]
        self.assertEqual(evaluate(e, TECH, now=NOW)["status"], "QUOTE_IDENTITY_BLOCKED")

    def test_missing_fee_evidence_blocks_before_math(self):
        e = dict(BROKER)
        del e["fee_evidence"]
        r = evaluate(e, TECH, now=NOW)
        self.assertEqual(r["status"], "FEE_EVIDENCE_BLOCKED")
        self.assertNotIn("net_profit_eur", r)

    def test_public_schedule_remains_hypothetical(self):
        r = evaluate(BROKER, TECH, now=NOW)
        self.assertEqual(r["fee_evidence_status"], "PUBLIC_FEE_ASSUMPTION_ONLY")
        self.assertFalse(r["degiro_fee_verified"])
        self.assertFalse(r["trade_ready"])

    def test_public_schedule_claiming_account_specific_blocks(self):
        e = {**BROKER, "fee_evidence": {
            "evidence_kind": "OFFICIAL_PUBLIC_SCHEDULE", "account_specific": True}}
        r = evaluate(e, TECH, now=NOW)
        self.assertEqual(r["status"], "FEE_EVIDENCE_BLOCKED")
        self.assertNotIn("net_profit_eur", r)

    def test_preview_claim_stays_unauthenticated(self):
        e = {**BROKER, "fee_evidence": {
            "evidence_kind": "BROKER_ORDER_PREVIEW",
            "sell_fee_basis": "UNVERIFIED_FUTURE_SELL_ESTIMATE",
            "preview_isin": BROKER["isin"],
            "preview_operating_mic": BROKER["operating_mic"],
            "preview_quantity": 53,
            "preview_buy_fee_eur": 4.9, "estimated_future_sell_fee_eur": 4.9}}
        r = evaluate(e, TECH, now=NOW)
        self.assertEqual(r["fee_evidence_status"], "UNAUTHENTICATED_ORDER_PREVIEW_CLAIM")
        self.assertFalse(r["degiro_fee_verified"])
        self.assertFalse(r["order_placement_enabled"])

    def test_preview_quantity_must_match_calculated_shares(self):
        e = {**BROKER, "fee_evidence": {
            "evidence_kind": "BROKER_ORDER_PREVIEW",
            "sell_fee_basis": "UNVERIFIED_FUTURE_SELL_ESTIMATE",
            "preview_isin": BROKER["isin"],
            "preview_operating_mic": BROKER["operating_mic"],
            "preview_quantity": 52,
            "preview_buy_fee_eur": 4.9, "estimated_future_sell_fee_eur": 4.9}}
        r = evaluate(e, TECH, now=NOW)
        self.assertEqual(r["status"], "FEE_PREVIEW_QUANTITY_BLOCKED")
        self.assertNotIn("net_profit_eur", r)

    def test_preview_wrong_venue_blocks_before_math(self):
        e = {**BROKER, "fee_evidence": {
            "evidence_kind": "BROKER_ORDER_PREVIEW",
            "sell_fee_basis": "UNVERIFIED_FUTURE_SELL_ESTIMATE",
            "preview_isin": BROKER["isin"],
            "preview_operating_mic": "XAMS", "preview_quantity": 53,
            "preview_buy_fee_eur": 4.9, "estimated_future_sell_fee_eur": 4.9}}
        r = evaluate(e, TECH, now=NOW)
        self.assertEqual(r["status"], "FEE_EVIDENCE_BLOCKED")
        self.assertNotIn("net_profit_eur", r)

    def test_preview_fee_difference_blocks(self):
        e = {**BROKER, "fee_evidence": {
            "evidence_kind": "BROKER_ORDER_PREVIEW",
            "sell_fee_basis": "UNVERIFIED_FUTURE_SELL_ESTIMATE",
            "preview_isin": BROKER["isin"],
            "preview_operating_mic": BROKER["operating_mic"],
            "preview_quantity": 53,
            "preview_buy_fee_eur": 4.91,
            "estimated_future_sell_fee_eur": 4.9}}
        r = evaluate(e, TECH, now=NOW)
        self.assertEqual(r["status"], "FEE_PREVIEW_AMOUNT_BLOCKED")
        self.assertNotIn("net_profit_eur", r)

    def test_missing_preview_fee_blocks(self):
        e = {**BROKER, "fee_evidence": {
            "evidence_kind": "BROKER_ORDER_PREVIEW",
            "sell_fee_basis": "UNVERIFIED_FUTURE_SELL_ESTIMATE",
            "preview_isin": BROKER["isin"],
            "preview_operating_mic": BROKER["operating_mic"],
            "preview_quantity": 53,
            "preview_buy_fee_eur": 4.9}}
        self.assertEqual(evaluate(e, TECH, now=NOW)["status"], "FEE_PREVIEW_AMOUNT_BLOCKED")

    def test_sell_estimate_mislabeled_as_preview_blocks(self):
        e = {**BROKER, "fee_evidence": {
            "evidence_kind": "BROKER_ORDER_PREVIEW",
            "sell_fee_basis": "UNVERIFIED_FUTURE_SELL_ESTIMATE",
            "preview_isin": BROKER["isin"],
            "preview_operating_mic": BROKER["operating_mic"],
            "preview_quantity": 53,
            "preview_buy_fee_eur": 4.9,
            "preview_sell_fee_eur": 4.9}}
        r = evaluate(e, TECH, now=NOW)
        self.assertEqual(r["reason"], "SELL_ESTIMATE_MISLABELED_AS_PREVIEW")
        self.assertNotIn("net_profit_eur", r)

    def test_nonfinite_preview_fee_blocks(self):
        e = {**BROKER, "fee_evidence": {
            "evidence_kind": "BROKER_ORDER_PREVIEW",
            "sell_fee_basis": "UNVERIFIED_FUTURE_SELL_ESTIMATE",
            "preview_isin": BROKER["isin"],
            "preview_operating_mic": BROKER["operating_mic"],
            "preview_quantity": 53,
            "preview_buy_fee_eur": float("nan"),
            "estimated_future_sell_fee_eur": 4.9}}
        self.assertEqual(evaluate(e, TECH, now=NOW)["status"], "FEE_PREVIEW_AMOUNT_BLOCKED")

    def test_preview_cannot_claim_future_sell_fee_verified(self):
        e = {**BROKER, "fee_evidence": {"evidence_kind": "BROKER_ORDER_PREVIEW", "preview_isin": BROKER["isin"], "preview_operating_mic": BROKER["operating_mic"], "preview_quantity": 53, "preview_buy_fee_eur": 4.9, "estimated_future_sell_fee_eur": 4.9, "sell_fee_basis": "VERIFIED"}}
        self.assertEqual(evaluate(e, TECH, now=NOW)["status"], "FEE_EVIDENCE_BLOCKED")

if __name__ == "__main__":
    unittest.main()
