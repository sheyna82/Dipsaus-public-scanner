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
            "verified": True, "source": "offline-test-only",
            "source_record_id": "fixture-" + name,
            "provider_id": "broker-fixture" if name == "broker" else "exchange-fixture",
            "source_family": "broker" if name == "broker" else "exchange",
            "source_url": "https://example.org/fixture/" + name,
            "checked_utc": NOW.isoformat(), "observed_price_usd": value, **({"formed_utc": "2026-11-02T10:00:00+00:00", "structure_still_valid": True} if name != "broker" else {})}
    return {
        "symbol": "TEST", "trade_ready": True, "rr_verified": True,
        "technical_evidence": technical,
        "money_inputs": {
            "budget_eur": 3500, "ask_usd": 52.05, "exit_bid_usd": 58.20,
            "invalidation_usd": 49, "eur_per_usd": 0.92,
            "buy_fee_eur": 2, "sell_fee_eur": 2,
            "buy_fx_rate": 0.0025, "sell_fx_rate": 0.0025,
        },
    }

class DecisionChainTests(unittest.TestCase):
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
