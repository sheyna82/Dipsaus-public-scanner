"""Regression tests for fail-closed recovery decision boundary."""
import json
import unittest
from pathlib import Path
from integrated_degiro_eligibility_gate import CONFIG
from integrated_recovery_decision_boundary import assess

class DecisionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(Path(CONFIG).read_text(encoding="utf-8"))
        cls.evidence = {"ASML": {"account_verified": True, "isin": "NL0010273215",
            "market": "Euronext Amsterdam", "liquidity_spread_costs_fx_verified": True}}
        cls.candidates = [{"symbol": "ASML", "trade_ready": False}]

    def test_default_fails_closed(self):
        row = assess(self.config, self.evidence, self.candidates)["candidates"][0]
        self.assertFalse(row["research_screen_allowed"])
        self.assertEqual(len(row["missing_evidence"]), 3)
        self.assertFalse(row["trade_ready"])

    def test_broker_not_verified_blocks_even_when_other_flags_true(self):
        row = assess(self.config, {}, self.candidates, True, True, True)["candidates"][0]
        self.assertIn("DEGIRO_INSTRUMENT_NOT_VERIFIED", row["missing_evidence"])

    def test_protocol_missing_blocks(self):
        row = assess(self.config, self.evidence, self.candidates, False, True, True)["candidates"][0]
        self.assertIn("FROZEN_PROTOCOL_NOT_VERIFIED", row["missing_evidence"])

    def test_market_data_missing_blocks(self):
        row = assess(self.config, self.evidence, self.candidates, True, False, True)["candidates"][0]
        self.assertIn("POINT_IN_TIME_MARKET_DATA_NOT_VERIFIED", row["missing_evidence"])

    def test_portfolio_missing_blocks(self):
        row = assess(self.config, self.evidence, self.candidates, True, True, False)["candidates"][0]
        self.assertIn("PORTFOLIO_NOT_RECONCILED", row["missing_evidence"])

    def test_all_verified_only_research_screen(self):
        result = assess(self.config, self.evidence, self.candidates, True, True, True)
        self.assertTrue(result["candidates"][0]["research_screen_allowed"])
        self.assertFalse(result["candidates"][0]["trade_ready"])
        self.assertFalse(result["trade_ready"])

    def test_non_boolean_evidence_flag_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_EVIDENCE_FLAGS"):
            assess(self.config, self.evidence, self.candidates, "yes", True, True)

    def test_unknown_symbol_never_passes(self):
        row = assess(self.config, {}, [{"symbol": "UNKNOWN", "trade_ready": False}],
                     True, True, True)["candidates"][0]
        self.assertFalse(row["research_screen_allowed"])

if __name__ == "__main__":
    unittest.main()
