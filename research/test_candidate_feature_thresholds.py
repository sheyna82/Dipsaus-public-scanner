"""Offline tests for fixed training-only feature threshold definitions."""
import unittest
from candidate_feature_thresholds import training_median_thresholds,label

def observation(x):
    return {"status":"DESCRIPTIVE_ONLY","relative_strength_20d_pct":x,
            "volume_ratio_20d":x,"atr_14_pct":x}

class ThresholdTests(unittest.TestCase):
    def test_train_only_thresholds_unaffected_by_future_rows(self):
        train=[(i,observation(float(i))) for i in range(40)]
        baseline=training_median_thresholds(train)
        self.assertEqual(baseline["status"],"TRAINING_ONLY_THRESHOLDS")
        future=[(i,observation(100000.0)) for i in range(40,70)]
        self.assertEqual(baseline,training_median_thresholds(train))
        self.assertNotEqual(baseline,training_median_thresholds(train+future))

    def test_insufficient_training_blocks(self):
        self.assertEqual(training_median_thresholds([(0,observation(1))])["status"],
                         "INSUFFICIENT_TRAINING_OBSERVATIONS")

    def test_feature_direction(self):
        train=[(i,observation(float(i))) for i in range(40)]
        threshold=training_median_thresholds(train)
        result=label(observation(25),threshold)
        self.assertTrue(result["passes"]["relative_strength_20d_pct"])
        self.assertTrue(result["passes"]["volume_ratio_20d"])
        self.assertFalse(result["passes"]["atr_14_pct"])
        self.assertFalse(result["trade_ready"])

if __name__=="__main__":unittest.main()
