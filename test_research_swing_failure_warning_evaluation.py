import unittest
from research_swing_failure_warning_evaluation import evaluate_failure_warnings
class WarningEvaluationTests(unittest.TestCase):
    def test_confusion_counts_and_no_warning(self):
        rows=[{"timestamp":i,"open":100,"high":101,"low":99,"close":100} for i in range(40)]
        r=evaluate_failure_warnings({"TEST":rows},horizon=5,step=5)
        self.assertEqual(r["tp"],0)
        self.assertEqual(r["fp"],0)
        self.assertEqual(r["fn"],0)
        self.assertEqual(r["tn"],3)
        self.assertIsNone(r["precision"])
        self.assertEqual(r["event_base_rate"],0)
        self.assertIsNone(r["precision_lift_vs_base_rate"])
    def test_warning_before_future_drawdown(self):
        rows=[{"timestamp":i,"open":100,"high":101,"low":99,"close":100} for i in range(40)]
        rows[20]={"timestamp":20,"open":99,"high":100,"low":90,"close":91}
        rows[21]={"timestamp":21,"open":90,"high":92,"low":80,"close":82}
        r=evaluate_failure_warnings({"TEST":rows},horizon=5,step=5)
        self.assertGreaterEqual(r["tp"],1)
    def test_invalid_horizon(self):
        with self.assertRaises(ValueError):
            evaluate_failure_warnings({},horizon=3)
if __name__=="__main__":
    unittest.main()
