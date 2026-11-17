"""No offline evidence combination may enable an actionable trade."""
import unittest
from research.us_shadow_decision_20261117 import assess_shadow_with_market_evidence

class ShadowDecisionTests(unittest.TestCase):
    def test_no_inputs_fail_closed(self):
        r = assess_shadow_with_market_evidence(None, None)
        self.assertIn("CANDIDATE_INPUT_MISSING", r["blocks"])
        self.assertIn("MARKET_EVIDENCE_MISSING", r["blocks"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["notify"])
        self.assertFalse(r["automatic_orders"])
    def test_empty_candidate_and_market_fail_closed(self):
        r = assess_shadow_with_market_evidence({}, {})
        self.assertEqual(r["status"], "SHADOW_BLOCKED")
        self.assertIn("MARKET_EVIDENCE_INVALID", r["blocks"])
        self.assertIn("CANDIDATE_NOT_CONFIRMED", r["blocks"])
    def test_independence_and_license_never_auto_granted(self):
        r = assess_shadow_with_market_evidence({}, None)
        self.assertIn("SOURCE_INDEPENDENCE_UNVERIFIED", r["blocks"])
        self.assertIn("DATA_LICENSE_UNVERIFIED", r["blocks"])
        self.assertIn("EXCHANGE_CALENDAR_UNVERIFIED", r["blocks"])
    def test_invalid_candidate_quote_type_fails_closed(self):
        r = assess_shadow_with_market_evidence({"quote": ["malformed"]}, None)
        self.assertEqual(r["status"], "SHADOW_BLOCKED")
        self.assertIn("CANDIDATE_quote_VALUE", r["blocks"])
        self.assertFalse(r["notify"])

    def test_invalid_candidate_timeframes_type_fails_closed(self):
        r = assess_shadow_with_market_evidence({"timeframes": 42}, None)
        self.assertEqual(r["status"], "SHADOW_BLOCKED")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["automatic_orders"])

    def test_symbol_mismatch_blocks_join(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "MSFT"})
        self.assertIn("INSTRUMENT_JOIN_SYMBOL_MISMATCH", r["blocks"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["notify"])

    def test_missing_candidate_symbol_blocks_join(self):
        r = assess_shadow_with_market_evidence({}, {"ticker": "AAPL"})
        self.assertIn("INSTRUMENT_JOIN_IDENTITY_MISSING", r["blocks"])

    def test_missing_market_symbol_blocks_join(self):
        r = assess_shadow_with_market_evidence({"symbol": "AAPL"}, {})
        self.assertIn("INSTRUMENT_JOIN_IDENTITY_MISSING", r["blocks"])

    def test_case_insensitive_symbol_join(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": " aapl "}, {"ticker": "AAPL"})
        self.assertNotIn("INSTRUMENT_JOIN_SYMBOL_MISMATCH", r["blocks"])
        self.assertNotIn("INSTRUMENT_JOIN_IDENTITY_MISSING", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_bad_market_payload_fails_closed(self):
        r = assess_shadow_with_market_evidence({}, {"payload": None})
        self.assertIn("MARKET_EVIDENCE_INVALID", r["blocks"])
        self.assertFalse(r["trade_ready"])

if __name__ == "__main__":
    unittest.main()
