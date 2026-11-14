"""Broker gating tests for research-only recovery candidate screening."""
import json
import unittest
from pathlib import Path
from integrated_degiro_eligibility_gate import CONFIG
from integrated_broker_candidate_screen import screen_candidates

class BrokerCandidateScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(Path(CONFIG).read_text(encoding="utf-8"))

    def test_unverified_recovery_candidate_blocked(self):
        result = screen_candidates(self.config, {}, [{"symbol": "ASML", "trade_ready": False}])
        self.assertFalse(result["candidates"][0]["research_screen_allowed"])
        self.assertFalse(result["trade_ready"])

    def test_verified_candidate_passes_research_screen_only(self):
        evidence = {"ASML": {"account_verified": True, "isin": "NL0010273215",
                    "market": "Euronext Amsterdam",
                    "liquidity_spread_costs_fx_verified": True}}
        result = screen_candidates(self.config, evidence, [{"symbol": "ASML", "trade_ready": False}])
        self.assertTrue(result["candidates"][0]["research_screen_allowed"])
        self.assertFalse(result["candidates"][0]["trade_ready"])

    def test_unknown_symbol_blocks(self):
        result = screen_candidates(self.config, {}, [{"symbol": "UNKNOWN", "trade_ready": False}])
        self.assertFalse(result["candidates"][0]["research_screen_allowed"])

    def test_unsupported_exchange_blocks_even_with_evidence(self):
        evidence = {"000660": {"account_verified": True, "isin": "KR7000660001",
                    "market": "Korea Exchange",
                    "liquidity_spread_costs_fx_verified": True}}
        result = screen_candidates(self.config, evidence, [{"symbol": "000660", "trade_ready": False}])
        self.assertFalse(result["candidates"][0]["research_screen_allowed"])

    def test_missing_research_only_flag_blocks(self):
        with self.assertRaisesRegex(ValueError, "RECOVERY_CANDIDATE_MUST_BE_RESEARCH_ONLY"):
            screen_candidates(self.config, {}, [{"symbol": "ASML"}])

    def test_duplicate_recovery_candidate_blocks(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_RECOVERY_CANDIDATE"):
            screen_candidates(self.config, {}, [{"symbol": "ASML", "trade_ready": False},
                                                {"symbol": "ASML", "trade_ready": False}])

if __name__ == "__main__":
    unittest.main()
