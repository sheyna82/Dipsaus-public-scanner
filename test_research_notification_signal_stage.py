import unittest
from research_notification_signal_stage import classify_stage
class StageTests(unittest.TestCase):
    def m(self,m5,m20,gap):
        return dict(status="historical_context_available",return_5_sessions_pct=m5,
                    return_20_sessions_pct=m20,distance_below_20_session_high_pct=gap,
                    recovery_from_20_session_low_pct=10)
    def test_momentum_not_mislabeled_early_recovery(self):
        self.assertEqual(classify_stage(self.m(4,11,0.2))["stage"],"MOMENTUM_NEAR_HIGH")
    def test_early_reversal_hypothesis(self):
        self.assertEqual(classify_stage(self.m(0.5,-8,9))["stage"],"POSSIBLE_EARLY_REVERSAL")
    def test_decline_not_trade_ready(self):
        r=classify_stage(self.m(-3,-3.5,4.5))
        self.assertEqual(r["stage"],"DOWNTREND_NOT_YET_CONFIRMED")
        self.assertFalse(r["trade_ready"])
    def test_missing_data(self):
        self.assertEqual(classify_stage({})["stage"],"UNCLASSIFIED")
if __name__=="__main__":unittest.main()
