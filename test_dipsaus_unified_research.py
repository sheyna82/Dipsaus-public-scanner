import unittest
from datetime import datetime, timezone, timedelta
from dipsaus_unified_research import evaluate, GATES

class UnifiedResearchTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026,10,19,14,tzinfo=timezone.utc)
    def test_missing_evidence_never_passes(self):
        result=evaluate({"symbol":"TEST"},{},self.now)
        self.assertEqual(len(result["unknown_gates"]),len(GATES))
        self.assertEqual(result["research_status"],"INCOMPLETE_RESEARCH")
        self.assertFalse(result["notify"])
        self.assertFalse(result["trade_ready"])
    def test_stale_pass_is_unknown(self):
        r=evaluate({},{"market_regime":{"status":"PASS","checked_utc":(self.now-timedelta(hours=1)).isoformat()}},self.now)
        self.assertEqual(r["checks"]["market_regime"]["status"],"UNKNOWN")
    def test_block_is_preserved(self):
        r=evaluate({},{"liquidity_execution":{"status":"BLOCK","checked_utc":self.now.isoformat()}},self.now)
        self.assertEqual(r["research_status"],"BLOCKED_RESEARCH")
        self.assertIn("liquidity_execution",r["blocked_gates"])
        self.assertFalse(r["automatic_orders"])
    def test_all_pass_still_not_trade_ready(self):
        evidence={gate:{"status":"PASS","checked_utc":self.now.isoformat()} for gate in GATES}
        r=evaluate({},evidence,self.now)
        self.assertEqual(r["research_status"],"REVIEW_REQUIRED")
        self.assertFalse(r["trade_ready"])
