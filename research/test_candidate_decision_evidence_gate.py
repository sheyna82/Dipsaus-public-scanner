import unittest
from candidate_decision_evidence_gate import assess, REQUIRED

class EvidenceGateTests(unittest.TestCase):
    def test_missing_evidence_blocks(self):
        row = assess({"symbol": "TEST"})
        self.assertEqual(row["status"], "INSUFFICIENT_EVIDENCE")
        self.assertFalse(row["trade_ready"])
        self.assertIn("MISSING_VALIDATED_ESTIMATES", row["missing_or_failed_gates"])

    def test_full_evidence_remains_manual(self):
        row = assess({"symbol": "TEST", "evidence": {k: True for k in REQUIRED},
                      "expected_net_return_pct": 1.1,
                      "expected_holding_sessions": 10,
                      "historical_mae_p10_pct": -7.0,
                      "validated_win_probability": .55})
        self.assertEqual(row["status"], "RESEARCH_REVIEW")
        self.assertFalse(row["automatic_orders"])
        self.assertFalse(row["trade_ready"])

    def test_false_gate_blocks(self):
        row = assess({"symbol": "TEST", "evidence": {k: True for k in REQUIRED if k != "data_quality_pass"}})
        self.assertIn("data_quality_pass", row["missing_or_failed_gates"])

    def test_rejects_fake_probability(self):
        with self.assertRaises(ValueError):
            assess({"symbol": "TEST", "validated_win_probability": 1.2})

    def test_rejects_nan(self):
        with self.assertRaises(ValueError):
            assess({"symbol": "TEST", "expected_net_return_pct": float("nan")})

if __name__ == "__main__":
    unittest.main()
