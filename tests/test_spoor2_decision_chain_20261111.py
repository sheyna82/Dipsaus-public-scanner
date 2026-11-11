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
            "checked_utc": NOW.isoformat(), "observed_price_usd": value}
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

    def test_missing_evidence_stays_research(self):
        row = valid_fixture()
        row["technical_evidence"].pop("resistance_evidence")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("RESISTANCE_EVIDENCE_MISSING", result["blocks"])
        self.assertEqual(result["notification_channel"], "RESEARCH")

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

    def test_bad_costs_fail_closed(self):
        row = valid_fixture()
        row["money_inputs"]["buy_fee_eur"] = float("nan")
        result = evaluate_research_chain(row, now_utc=NOW)
        self.assertIn("MONEY_CALCULATION_BLOCKED", result["blocks"])
        self.assertFalse(result["trade_ready"])

if __name__ == "__main__":
    unittest.main()
