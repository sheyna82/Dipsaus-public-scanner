"""Offline checks for single-feature ablation safety and cohort accounting."""
import unittest
from candidate_feature_ablation import evaluate_ablation, FILTERS

def rows(n=200, factor=1.03):
    return [{"timestamp":1700000000+i*86400,
             "open":100*factor**i,"close":100*factor**i,
             "high":101*factor**i,"low":99*factor**i,
             "volume":1000+i*5} for i in range(n)]

class AblationTests(unittest.TestCase):
    def test_missing_benchmark_blocks(self):
        result=evaluate_ablation(rows(),[],"breakout_prior20")
        self.assertFalse(result["trade_ready"])
        self.assertNotEqual(result["status"],"DESCRIPTIVE_ONLY")

    def test_flat_prices_no_training_signals(self):
        result=evaluate_ablation(rows(factor=1),rows(factor=1),"breakout_prior20")
        self.assertEqual(result["status"],"INSUFFICIENT_TRAINING_OBSERVATIONS")

    def test_risk_diagnostics_wired_to_ablation(self):
        from unittest.mock import patch
        import candidate_feature_ablation as module
        stock=rows(200,1.03)
        benchmark=rows(200,1.001)
        with patch.object(module, 'MIN_TRAIN', 40), patch.object(module, 'features', return_value={'breakout_prior20':True}), patch.object(module, 'pre_entry_features', return_value={'relative_strength_20d_pct':1,'volume_ratio_20d':2,'atr_14_pct':1}), patch.object(module, 'training_median_thresholds', return_value={'status':'TRAINING_ONLY_THRESHOLDS','thresholds':{}}), patch.object(module, 'label', return_value={'status':'RESEARCH_ONLY','passes':{'relative_strength_20d_pct':True,'volume_ratio_20d':True,'atr_14_pct':True}}):
            result=module.evaluate_ablation(stock,benchmark,'breakout_prior20')
        self.assertEqual(result['status'],'DESCRIPTIVE_ONLY')
        risk=result['risk_diagnostics']
        self.assertFalse(risk['trade_ready'])
        self.assertEqual(risk['filters']['baseline']['n'],result['cohorts']['baseline']['n'])
        self.assertIsInstance(risk['filters']['baseline']['mean_net_pct'],float)
        self.assertIn('mae_breach_fraction',risk['filters']['baseline'])
        execution=result['execution_sensitivity']['baseline']
        self.assertFalse(execution['trade_ready'])
        self.assertEqual(execution['n']+execution['blocked_n'],result['cohorts']['baseline']['n'])
        if execution['n']:
            vals=execution['mean_net_pct_by_entry_slippage_bps']
            self.assertGreaterEqual(vals['0'],vals['50'])

    def test_cohort_keys_predeclared(self):
        self.assertEqual(len(FILTERS),5)
        self.assertIn("all_three",FILTERS)
        self.assertIn("baseline",FILTERS)

if __name__=="__main__":unittest.main()
