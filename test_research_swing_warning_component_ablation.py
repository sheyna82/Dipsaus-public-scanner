import unittest
from research_swing_warning_component_ablation import evaluate_warning_components, SIGNALS

class ComponentAblationTests(unittest.TestCase):
    def test_flat_prices(self):
        rows=[{"timestamp":i,"open":100,"high":101,"low":99,"close":100} for i in range(50)]
        result=evaluate_warning_components({"FLAT":rows}, horizon=5, step=5)
        self.assertEqual(result["observations"],5)
        for name in SIGNALS:
            self.assertEqual(result["components"][name]["all"]["tp"],0)
            self.assertEqual(result["components"][name]["all"]["fp"],0)
            self.assertIsNone(result["components"][name]["all"]["precision"])
        self.assertFalse(result["trade_ready"])

    def test_gap_warning_and_later_loss(self):
        rows=[{"timestamp":i,"open":100,"high":101,"low":99,"close":100} for i in range(50)]
        rows[20]={"timestamp":20,"open":94,"high":95,"low":90,"close":92}
        rows[21]={"timestamp":21,"open":91,"high":92,"low":80,"close":82}
        result=evaluate_warning_components({"GAP":rows}, horizon=5, step=5)
        self.assertGreaterEqual(result["components"]["gap"]["all"]["tp"],1)
        self.assertGreaterEqual(result["components"]["combined"]["all"]["tp"],1)

    def test_invalid_horizon(self):
        with self.assertRaises(ValueError):
            evaluate_warning_components({}, horizon=3)

if __name__=="__main__":
    unittest.main()
