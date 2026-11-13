import unittest
from research.spoor2_execution_evidence_gate_20261113 import assess_execution_evidence

RECORDS = [{"isin": "DE0006231004", "mic_code": "XETR", "market_segment_code": "045"},
           {"isin": "DE0007030009", "mic_code": "XETR", "market_segment_code": "045"}]

class TestExecutionEvidenceGate(unittest.TestCase):
    def test_pilot_remains_blocked(self):
        result = assess_execution_evidence({"status": "BLOCKED", "records": RECORDS})
        self.assertEqual(len(result["instruments"]), 2)
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["order_placement_enabled"])
        self.assertFalse(result["segment_mic_verified"])
        self.assertFalse(result["broker_route_verified"])
        self.assertFalse(result["degiro_fee_verified"])

    def test_untrusted_claims_cannot_promote(self):
        claim = {"verified": True, "mic": "XETR", "source": "self-asserted"}
        result = assess_execution_evidence({"status": "BLOCKED", "records": RECORDS},
                                           mic_evidence=claim, broker_evidence=claim,
                                           fee_evidence=claim)
        self.assertFalse(result["trade_ready"])
        self.assertTrue(all(i["degiro_execution_route"] is None for i in result["instruments"]))

    def test_missing_pilot_blocks(self):
        result = assess_execution_evidence({"status": "BLOCKED", "records": RECORDS[:1]})
        self.assertIn("INCOMPLETE_PILOT_INSTRUMENTS", result["blocks"])

    def test_wrong_mic_blocks(self):
        records = [dict(x) for x in RECORDS]
        records[0]["mic_code"] = "XAMS"
        result = assess_execution_evidence({"status": "BLOCKED", "records": records})
        self.assertIn("UNEXPECTED_XETRA_INSTRUMENT_DE0006231004", result["blocks"])

    def test_malformed_record_blocks_without_exception(self):
        result = assess_execution_evidence({"status": "BLOCKED", "records": [None, RECORDS[1]]})
        self.assertIn("INVALID_PILOT_ISIN_SET", result["blocks"])
        self.assertFalse(result["trade_ready"])

if __name__ == "__main__":
    unittest.main()
