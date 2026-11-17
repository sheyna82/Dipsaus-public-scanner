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
    def test_bad_market_payload_fails_closed(self):
        r = assess_shadow_with_market_evidence({}, {"payload": None})
        self.assertIn("MARKET_EVIDENCE_INVALID", r["blocks"])
        self.assertFalse(r["trade_ready"])

if __name__ == "__main__":
    unittest.main()
