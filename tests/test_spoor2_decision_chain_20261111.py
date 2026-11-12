"""Spoor 2 decision chain regression: malicious readiness claims stay research."""
import unittest
from datetime import datetime, timezone
from research.spoor2_decision_chain_20261111 import evaluate_research_chain

NOW = datetime(2026, 11, 11, 10, tzinfo=timezone.utc)

def valid_fixture():
    technical = {"broker_ask_usd": 52.05, "invalidation_usd": 49,
                 "resistance_usd": 58.20}
    for name, value in (("broker", 52.05), ("invalidation", 49),
                        ("resistance", 58.20)):
        technical[name + "_evidence"] = {
            "verified": True, "source": "offline-test-only", "symbol": "TEST",
            "market": "US", "venue_mic": "XNAS", "isin": "US0378331005",
            "source_record_id": "fixture-" + name,
            "provider_id": "broker-fixture" if name == "broker" else "exchange-fixture",
            "source_family": "broker" if name == "broker" else "exchange",
            "source_url": "https://example.org/fixture/" + name,
            "checked_utc": NOW.isoformat(), "observed_price_usd": value, **({"formed_utc": "2026-11-02T10:00:00+00:00", "structure_still_valid": True} if name != "broker" else {})}
    return {
        "symbol": "TEST", "market": "US", "quote_currency": "USD",
        "venue_mic": "XNAS", "isin": "US0378331005",
        "trade_ready": True, "rr_verified": True,
        "technical_evidence": technical,
        "money_inputs": {
            "budget_eur": 3500, "ask_usd": 52.05, "exit_bid_usd": 58.20,
            "invalidation_usd": 49, "eur_per_usd": 0.92,
            "buy_fee_eur": 2, "sell_fee_eur": 2,
            "buy_fx_rate": 0.0025, "sell_fx_rate": 0.0025,
        },
    }

class DecisionChainTests(unittest.TestCase):
    def test_integrated_identity_mismatch_is_reported_and_blocked(self):
        row = valid_fixture()
        row["venue_mic"] = "XNAS"
        row["isin"] = "US0378331005"
        for role in ("broker", "invalidation", "resistance"):
            row["technical_evidence"][role + "_evidence"].update({
                "market": "US", "venue_mic": "XNAS", "isin": "US0378331005"})
        row["technical_evidence"]["resistance_evidence"]["venue_mic"] = "XNYS"
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("RESISTANCE_VENUE_MIC_MISMATCH", result["blocks"])
        self.assertEqual(result["instrument_identity_audit"]["status"], "BLOCKED")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["offline_notification_route"]["send_enabled"])

    def test_integrated_consistent_identity_is_still_unattested(self):
        row = valid_fixture()
        row["venue_mic"] = "XNAS"
        row["isin"] = "US0378331005"
        for role in ("broker", "invalidation", "resistance"):
            row["technical_evidence"][role + "_evidence"].update({
                "market": "US", "venue_mic": "XNAS", "isin": "US0378331005"})
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertEqual(result["instrument_identity_audit"]["status"],
                         "CONSISTENT_CLAIMS_NOT_EXTERNALLY_ATTESTED")
        self.assertIn("EXTERNAL_INSTRUMENT_ATTESTATION_NOT_CONNECTED", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_missing_signed_evidence_blocks_chain(self):
        result = evaluate_research_chain(valid_fixture(), now_utc=NOW)
        self.assertIn("INSTRUMENT_SIGNED_EVIDENCE_MISSING", result["blocks"])
        self.assertFalse(result["instrument_signature_audit"]["source_attested"])
        self.assertFalse(result["trade_ready"])

    def test_self_claimed_signature_does_not_authorize_chain(self):
        row = valid_fixture()
        row["instrument_signed_evidence"] = {
            "signed_record": {key: row[key] for key in
                              ("symbol", "market", "venue_mic", "isin")},
            "signature_b64": "not-a-signature",
            "signer_public_key_b64": "not-a-key",
            "signature_verified": True,
            "source_attested": True,
        }
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("INVALID_INSTRUMENT_SIGNATURE_ENCODING", result["blocks"])
        self.assertFalse(result["instrument_signature_audit"]["source_attested"])
        self.assertFalse(result["offline_notification_route"]["send_enabled"])

    def test_missing_bound_observation_blocks_chain(self):
        result = evaluate_research_chain(valid_fixture(), now_utc=NOW)
        self.assertIn("INSTRUMENT_BOUND_OBSERVATION_MISSING", result["blocks"])
        self.assertFalse(result["instrument_bound_observation_audit"]["source_attested"])
        self.assertFalse(result["trade_ready"])

    def test_self_claimed_bound_observation_does_not_authorize_chain(self):
        row = valid_fixture()
        row["instrument_bound_observation"] = {
            "signed_record": {**{key: row[key] for key in
                                ("symbol", "market", "venue_mic", "isin")},
                              "observed_utc": "2026-11-11T09:59:00Z",
                              "challenge_nonce": "a" * 32},
            "signature_b64": "not-a-signature",
            "signer_public_key_b64": "not-a-key",
            "signature_verified": True,
            "replay_prevented": True,
        }
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("INVALID_BOUND_INSTRUMENT_SIGNATURE_ENCODING", result["blocks"])
        self.assertFalse(result["instrument_bound_observation_audit"]["replay_prevented"])
        self.assertFalse(result["offline_notification_route"]["send_enabled"])

    def test_even_claimed_verified_stays_research(self):
        result = evaluate_research_chain(valid_fixture(), now_utc=NOW)
        self.assertEqual(result["notification_channel"], "RESEARCH")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["order_placement_enabled"])
        self.assertIn("INDEPENDENT_TRADE_ATTESTATION_NOT_CONNECTED", result["blocks"])
        self.assertIn("GEEN KOOP", result["notification_subject"])

    def test_decision_chain_never_routes_to_live_ntfy(self):
        result = evaluate_research_chain(valid_fixture(), now_utc=NOW)
        route = result["offline_notification_route"]
        self.assertEqual(route["route"], "RESEARCH_ONLY")
        self.assertFalse(route["send_enabled"])
        self.assertFalse(route["topic_configured"])
        self.assertFalse(result["trade_ready"])

    def test_end_to_end_entry_zone_finance_and_route_remain_offline(self):
        result = evaluate_research_chain(valid_fixture(), now_utc=NOW)
        self.assertEqual(result["entry_zone_research"]["status"],
                         "ILLUSTRATIVE_ENTRY_ZONE_ONLY")
        self.assertEqual(result["money_scenario"]["status"],
                         "ILLUSTRATIVE_NOT_VERIFIED")
        self.assertIn("NET_SCENARIO_RR_BELOW_TWO", result["blocks"])
        self.assertEqual(result["offline_notification_route"]["route"],
                         "RESEARCH_ONLY")
        self.assertFalse(result["offline_notification_route"]["send_enabled"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["order_placement_enabled"])

    def test_end_to_end_insufficient_entry_room_fails_closed(self):
        row = valid_fixture()
        row["technical_evidence"]["resistance_usd"] = 54
        row["technical_evidence"]["resistance_evidence"]["observed_price_usd"] = 54
        row["money_inputs"]["exit_bid_usd"] = 54
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertEqual(result["entry_zone_research"]["status"],
                         "REFERENCE_RR_BELOW_MINIMUM")
        self.assertIn("RESEARCH_ENTRY_ZONE_NOT_ESTABLISHED",result["blocks"])
        self.assertEqual(result["offline_notification_route"]["route"],
                         "RESEARCH_ONLY")
        self.assertFalse(result["trade_ready"])

    def test_mathematical_zone_does_not_override_missing_provenance(self):
        row = valid_fixture()
        row["technical_evidence"]["resistance_evidence"].pop("source_record_id")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertEqual(result["entry_zone_research"]["status"],
                         "ILLUSTRATIVE_ENTRY_ZONE_ONLY")
        self.assertIn("ENTRY_ZONE_EVIDENCE_INCOMPLETE",result["blocks"])
        self.assertEqual(result["offline_notification_route"]["route"],
                         "RESEARCH_ONLY")
        self.assertFalse(result["trade_ready"])

    def test_mathematical_zone_does_not_override_stale_quote(self):
        row = valid_fixture()
        row["technical_evidence"]["broker_evidence"]["checked_utc"] = (
            "2026-11-10T10:00:00+00:00")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertEqual(result["entry_zone_research"]["status"],
                         "ILLUSTRATIVE_ENTRY_ZONE_ONLY")
        self.assertIn("BROKER_STALE_OR_FUTURE",result["blocks"])
        self.assertIn("ENTRY_ZONE_EVIDENCE_INCOMPLETE",result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_observed_price_tampering_blocks_even_if_math_is_valid(self):
        row = valid_fixture()
        row["technical_evidence"]["resistance_evidence"]["observed_price_usd"] = 62
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertEqual(result["entry_zone_research"]["status"],
                         "ILLUSTRATIVE_ENTRY_ZONE_ONLY")
        self.assertIn("RESISTANCE_PRICE_MISMATCH", result["blocks"])
        self.assertIn("ENTRY_ZONE_EVIDENCE_INCOMPLETE", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_future_quote_timestamp_blocks_even_if_math_is_valid(self):
        row = valid_fixture()
        row["technical_evidence"]["broker_evidence"]["checked_utc"] = (
            "2026-11-12T10:00:00+00:00")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("BROKER_STALE_OR_FUTURE", result["blocks"])
        self.assertIn("ENTRY_ZONE_EVIDENCE_INCOMPLETE", result["blocks"])
        self.assertFalse(result["offline_notification_route"]["send_enabled"])

    def test_reused_broker_source_family_blocks_independent_review(self):
        row = valid_fixture()
        row["technical_evidence"]["resistance_evidence"]["source_family"] = "broker"
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("BROKER_TECHNICAL_SOURCE_FAMILY_NOT_INDEPENDENT",
                      result["blocks"])
        self.assertIn("ENTRY_ZONE_EVIDENCE_INCOMPLETE", result["blocks"])
        self.assertEqual(result["offline_notification_route"]["route"],
                         "RESEARCH_ONLY")
        self.assertFalse(result["trade_ready"])

    def test_missing_evidence_stays_research(self):
        row = valid_fixture()
        row["technical_evidence"].pop("resistance_evidence")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("RESISTANCE_EVIDENCE_MISSING", result["blocks"])
        self.assertEqual(result["notification_channel"], "RESEARCH")

    def test_same_provider_is_blocked_in_decision_chain(self):
        row = valid_fixture()
        row["technical_evidence"]["invalidation_evidence"]["provider_id"] = "broker-fixture"
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("BROKER_TECHNICAL_PROVIDER_NOT_INDEPENDENT", result["blocks"])
        self.assertEqual(result["source_independence_audit"]["status"], "BLOCKED")
        self.assertFalse(result["trade_ready"])

    def test_missing_provenance_is_blocked_in_decision_chain(self):
        row = valid_fixture()
        row["technical_evidence"]["broker_evidence"].pop("source_record_id")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("BROKER_PROVENANCE_INCOMPLETE", result["blocks"])

    def test_independent_fixture_still_requires_external_attestation(self):
        result = evaluate_research_chain(valid_fixture(), now_utc=NOW)
        self.assertEqual(result["source_independence_audit"]["status"],
                         "PROVENANCE_RECORDED_REQUIRES_EXTERNAL_VERIFICATION")
        self.assertIn("INDEPENDENT_TRADE_ATTESTATION_NOT_CONNECTED", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_european_gbp_pence_never_enters_usd_chain(self):
        row = valid_fixture()
        row["market"] = "EU"
        row["quote_currency"] = "GBp"
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("MARKET_NOT_SUPPORTED_BY_USD_CHAIN", result["blocks"])
        self.assertIn("QUOTE_CURRENCY_NOT_USD", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_eur_quote_never_enters_usd_chain(self):
        row = valid_fixture()
        row["market"] = "US"
        row["quote_currency"] = "EUR"
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("QUOTE_CURRENCY_NOT_USD", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_undeclared_market_and_currency_fail_closed(self):
        row = valid_fixture()
        row.pop("market")
        row.pop("quote_currency")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("MARKET_NOT_DECLARED_FOR_USD_CHAIN", result["blocks"])
        self.assertIn("QUOTE_CURRENCY_NOT_DECLARED_FOR_USD_CHAIN", result["blocks"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["offline_notification_route"]["send_enabled"])

    def test_explicit_usd_market_avoids_declaration_blocks(self):
        row = valid_fixture()
        row["market"] = "US"
        row["quote_currency"] = "USD"
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertNotIn("MARKET_NOT_DECLARED_FOR_USD_CHAIN", result["blocks"])
        self.assertNotIn("QUOTE_CURRENCY_NOT_DECLARED_FOR_USD_CHAIN", result["blocks"])
        self.assertIn("INDEPENDENT_TRADE_ATTESTATION_NOT_CONNECTED", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_partially_declared_currency_fails_closed(self):
        row = valid_fixture()
        row["market"] = "US"
        row.pop("quote_currency")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("QUOTE_CURRENCY_NOT_DECLARED_FOR_USD_CHAIN", result["blocks"])
        self.assertFalse(result["order_placement_enabled"])

    def test_price_evidence_for_another_instrument_is_blocked(self):
        row = valid_fixture()
        row["technical_evidence"]["resistance_evidence"]["symbol"] = "OTHER"
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("RESISTANCE_INSTRUMENT_MISMATCH", result["blocks"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["offline_notification_route"]["send_enabled"])

    def test_undeclared_instrument_on_price_record_is_blocked(self):
        row = valid_fixture()
        row["technical_evidence"]["broker_evidence"].pop("symbol")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("BROKER_INSTRUMENT_NOT_DECLARED", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_all_matching_instrument_records_avoid_binding_blocks(self):
        row = valid_fixture()
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertFalse(any(block.endswith(("INSTRUMENT_MISMATCH", "INSTRUMENT_NOT_DECLARED")) for block in result["blocks"]))
        self.assertIn("INDEPENDENT_TRADE_ATTESTATION_NOT_CONNECTED", result["blocks"])

    def test_missing_money_inputs_stays_research(self):
        row = valid_fixture()
        row.pop("money_inputs")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("MONEY_INPUTS_MISSING", result["blocks"])

    def test_invalid_symbol_blocks_entirely(self):
        self.assertEqual(evaluate_research_chain({}, now_utc=NOW)["notification_channel"], "NONE")
        self.assertEqual(evaluate_research_chain(None, now_utc=NOW)["notification_channel"], "NONE")

    def test_low_rr_never_qualifies(self):
        row = valid_fixture()
        row["money_inputs"]["exit_bid_usd"] = 54
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("SCENARIO_RR_BELOW_TWO", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_gross_two_r_does_not_override_net_friction_gate(self):
        row = valid_fixture()
        row["technical_evidence"]["resistance_usd"] = 58.15
        row["technical_evidence"]["resistance_evidence"]["observed_price_usd"] = 58.15
        row["money_inputs"]["exit_bid_usd"] = 58.15
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertAlmostEqual(result["money_scenario"]["reference_rr"], 2)
        self.assertLess(result["money_scenario"]["net_reference_rr_after_friction"], 2)
        self.assertIn("NET_SCENARIO_RR_BELOW_TWO", result["blocks"])
        self.assertEqual(result["notification_channel"], "RESEARCH")
        self.assertFalse(result["trade_ready"])

    def test_net_gate_is_separate_from_gross_gate(self):
        row = valid_fixture()
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertNotIn("SCENARIO_RR_BELOW_TWO", result["blocks"])
        self.assertIn("NET_SCENARIO_RR_BELOW_TWO", result["blocks"])
        self.assertFalse(result["order_placement_enabled"])

    def test_net_profit_just_below_150_cannot_round_into_qualification(self):
        row = valid_fixture()
        row["market"] = "US"
        row["quote_currency"] = "USD"
        from research.spoor2_candidate_levels_20261111 import money_scenario
        inputs = row["money_inputs"]
        shares = money_scenario(**inputs)["whole_shares"]
        buy_total = (shares * inputs["ask_usd"] * inputs["eur_per_usd"]
                     * (1 + inputs["buy_fx_rate"]) + inputs["buy_fee_eur"])
        target = ((buy_total + 149.999 + inputs["sell_fee_eur"])
                  / (shares * inputs["eur_per_usd"]
                     * (1 - inputs["sell_fx_rate"])))
        row["technical_evidence"]["resistance_usd"] = target
        row["technical_evidence"]["resistance_evidence"]["observed_price_usd"] = target
        row["money_inputs"]["exit_bid_usd"] = target
        result = evaluate_research_chain(row, now_utc=NOW)
        scenario = result["money_scenario"]
        self.assertLess(scenario["net_profit_eur_unrounded"], 150)
        self.assertEqual(scenario["net_profit_eur"], 150.0)
        self.assertIn("NET_PROFIT_BELOW_150", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_gross_rr_just_below_two_cannot_round_into_qualification(self):
        row = valid_fixture()
        row["market"] = "US"
        row["quote_currency"] = "USD"
        ask = row["money_inputs"]["ask_usd"]
        invalidation = row["money_inputs"]["invalidation_usd"]
        # Gross RR = 1.99999, which rounds to 2.0000 for display.
        resistance = ask + 1.99999 * (ask - invalidation)
        row["technical_evidence"]["resistance_usd"] = resistance
        row["technical_evidence"]["resistance_evidence"]["observed_price_usd"] = resistance
        row["money_inputs"]["exit_bid_usd"] = resistance
        result = evaluate_research_chain(row, now_utc=NOW)
        scenario = result["money_scenario"]
        self.assertLess(scenario["reference_rr_unrounded"], 2)
        self.assertEqual(scenario["reference_rr"], 2.0)
        self.assertIn("SCENARIO_RR_BELOW_TWO", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_net_rr_just_below_two_cannot_round_into_qualification(self):
        row = valid_fixture()
        row["market"] = "US"
        row["quote_currency"] = "USD"
        # Find a resistance where exact net R/R is just below two,
        # while the four-decimal display value rounds to 2.0000.
        from research.spoor2_candidate_levels_20261111 import money_scenario
        low, high = 58.0, 65.0
        for _ in range(60):
            mid = (low + high) / 2
            inputs = {**row["money_inputs"], "exit_bid_usd": mid}
            value = money_scenario(**inputs)["net_reference_rr_unrounded"]
            if value < 1.99999:
                low = mid
            else:
                high = mid
        target = (low + high) / 2
        row["technical_evidence"]["resistance_usd"] = target
        row["technical_evidence"]["resistance_evidence"]["observed_price_usd"] = target
        row["money_inputs"]["exit_bid_usd"] = target
        result = evaluate_research_chain(row, now_utc=NOW)
        scenario = result["money_scenario"]
        self.assertLess(scenario["net_reference_rr_unrounded"], 2)
        self.assertEqual(scenario["net_reference_rr_after_friction"], 2.0)
        self.assertIn("NET_SCENARIO_RR_BELOW_TWO", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_money_prices_cannot_differ_from_audited_levels(self):
        for money_field, replacement, expected in (
            ("ask_usd", 53, "ENTRY_EVIDENCE_MISMATCH"),
            ("invalidation_usd", 48, "INVALIDATION_EVIDENCE_MISMATCH"),
            ("exit_bid_usd", 62, "EXIT_RESISTANCE_EVIDENCE_MISMATCH"),
        ):
            row = valid_fixture()
            row["money_inputs"][money_field] = replacement
            result = evaluate_research_chain(row, now_utc=NOW)
            self.assertIn(expected, result["blocks"])
            self.assertFalse(result["trade_ready"])

    def test_bad_costs_fail_closed(self):
        row = valid_fixture()
        row["money_inputs"]["buy_fee_eur"] = float("nan")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("MONEY_CALCULATION_BLOCKED", result["blocks"])
        self.assertFalse(result["trade_ready"])

if __name__ == "__main__":
    unittest.main()
