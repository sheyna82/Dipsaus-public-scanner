import unittest
from research_europe_registry_receipt_demo import demonstrate
class Tests(unittest.TestCase):
    def test_synthetic_receipt_and_tamper(self):
        result=demonstrate()
        self.assertTrue(result["synthetic_fixture"])
        self.assertTrue(result["tamper_detected"])
        self.assertFalse(result["minimum_observation_met"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["orders_placed"])
        self.assertFalse(result["live_benchmark_identity_verified"])
        self.assertEqual(len(result["decision_sha256"]),64)
    def test_deterministic(self):
        self.assertEqual(demonstrate(),demonstrate())
if __name__=="__main__":unittest.main()
