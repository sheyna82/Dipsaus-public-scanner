import unittest
from research_swing_exit_policy_ab import simulate_exit_policies, compare_exit_policies

class ExitPolicyTests(unittest.TestCase):
    def bars(self):
        return [{"timestamp":i,"open":100,"high":101,"low":99,"close":100} for i in range(65)]

    def test_flat_all_equal_after_costs(self):
        rows=self.bars()
        result=simulate_exit_policies(rows,20,10)
        self.assertEqual(result["baseline_net_pct"],-.3)
        self.assertEqual(result["warning_exit_net_pct"],-.3)
        self.assertEqual(result["partial_profit_net_pct"],-.3)
        self.assertIsNone(result["warning_exit_index"])

    def test_warning_exits_only_after_close(self):
        rows=self.bars()
        rows[23]={"timestamp":23,"open":94,"high":95,"low":90,"close":92}
        rows[24]={"timestamp":24,"open":89,"high":90,"low":85,"close":88}
        result=simulate_exit_policies(rows,20,10)
        self.assertEqual(result["warning_exit_index"],24)
        self.assertAlmostEqual(result["warning_exit_net_pct"],-11.3)

    def test_partial_profit_fills_next_open_not_high(self):
        rows=self.bars()
        rows[22]={"timestamp":22,"open":100,"high":110,"low":99,"close":106}
        rows[23]={"timestamp":23,"open":104,"high":105,"low":100,"close":103}
        result=simulate_exit_policies(rows,20,10)
        self.assertEqual(result["partial_profit_exit_index"],23)
        self.assertAlmostEqual(result["partial_profit_net_pct"],1.7)

    def test_severe_loss_and_median_are_reported(self):
        rows=self.bars()
        rows[30]={"timestamp":30,"open":80,"high":81,"low":79,"close":80}
        result=compare_exit_policies({"A":rows},horizon=10,step=15)
        baseline=result["policies"]["baseline"]
        self.assertIn("median_net_pct",baseline)
        self.assertGreaterEqual(baseline["loss_worse_than_8pct"],1)
        self.assertFalse(result["portfolio_overlap_modelled"])
        self.assertFalse(result["universe_selection_modelled"])

    def test_comparison_requires_nonoverlap(self):
        with self.assertRaises(ValueError):
            compare_exit_policies({"A":self.bars()},horizon=10,step=5)

if __name__=="__main__":
    unittest.main()
