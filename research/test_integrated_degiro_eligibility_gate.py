"""Offline tests for research-only broker instrument gate."""
import json
import unittest
from pathlib import Path
from copy import deepcopy
from integrated_degiro_eligibility_gate import evaluate, CONFIG

class BrokerGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(Path(CONFIG).read_text(encoding="utf-8"))

    def test_all_unverified_candidates_blocked(self):
        result = evaluate(self.config)
        self.assertEqual(len(result["candidates"]), 10)
        self.assertFalse(result["trade_ready"])
        self.assertTrue(all(not c["eligible_for_recovery_screen"] for c in result["candidates"]))

    def test_verified_supported_instrument_is_research_only(self):
        evidence = {"ASML": {"account_verified": True, "isin": "NL0010273215",
                             "market": "Euronext Amsterdam",
                             "liquidity_spread_costs_fx_verified": True}}
        result = evaluate(self.config, evidence)
        row = next(c for c in result["candidates"] if c["symbol"] == "ASML")
        self.assertTrue(row["eligible_for_recovery_screen"])
        self.assertFalse(row["trade_ready"])

    def test_unverified_exchange_remains_blocked_even_with_evidence(self):
        evidence = {"000660": {"account_verified": True, "isin": "KR7000660001",
                               "market": "Korea Exchange",
                               "liquidity_spread_costs_fx_verified": True}}
        row = next(c for c in evaluate(self.config, evidence)["candidates"] if c["symbol"] == "000660")
        self.assertFalse(row["eligible_for_recovery_screen"])

    def test_missing_cost_evidence_blocks(self):
        evidence = {"ASML": {"account_verified": True, "isin": "NL0010273215",
                             "market": "Euronext Amsterdam"}}
        self.assertFalse(evaluate(self.config, evidence)["candidates"][0]["eligible_for_recovery_screen"])

    def test_market_mismatch_blocks(self):
        evidence = {"ASML": {"account_verified": True, "isin": "NL0010273215",
                             "market": "Nasdaq", "liquidity_spread_costs_fx_verified": True}}
        self.assertFalse(evaluate(self.config, evidence)["candidates"][0]["eligible_for_recovery_screen"])

    def test_invalid_isin_blocks(self):
        evidence = {"ASML": {"account_verified": True, "isin": "ASML",
                             "market": "Euronext Amsterdam", "liquidity_spread_costs_fx_verified": True}}
        self.assertFalse(evaluate(self.config, evidence)["candidates"][0]["eligible_for_recovery_screen"])

    def test_unsafe_trade_ready_blocks(self):
        config = deepcopy(self.config)
        config["trade_ready"] = True
        with self.assertRaisesRegex(ValueError, "UNSAFE_ELIGIBILITY_CONFIG"):
            evaluate(config)

    def test_unsafe_order_setting_blocks(self):
        config = deepcopy(self.config)
        config["portfolio_constraints"]["orders"] = "AUTOMATIC"
        with self.assertRaisesRegex(ValueError, "AUTOMATED_ORDERS_NOT_ALLOWED"):
            evaluate(config)

    def test_duplicate_symbol_blocks(self):
        config = deepcopy(self.config)
        config["candidates"].append(deepcopy(config["candidates"][0]))
        with self.assertRaisesRegex(ValueError, "DUPLICATE_SYMBOL"):
            evaluate(config)

    def test_unknown_status_blocks(self):
        config = deepcopy(self.config)
        config["candidates"][0]["status"] = "ELIGIBLE"
        with self.assertRaisesRegex(ValueError, "UNKNOWN_EXCHANGE_STATUS"):
            evaluate(config)

if __name__ == "__main__":
    unittest.main()
