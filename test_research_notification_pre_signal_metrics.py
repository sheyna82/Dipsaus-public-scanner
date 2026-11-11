import unittest
from datetime import datetime, timezone, timedelta
from research_notification_pre_signal_metrics import pre_signal_metrics

class PreSignalMetricTests(unittest.TestCase):
    def setUp(self):
        start=datetime(2026,9,1,tzinfo=timezone.utc)
        self.bars=[{"timestamp":int((start+timedelta(days=i)).timestamp()),
                    "open":100+i,"high":110+i,"low":90+i,"close":100+i}
                   for i in range(40)]

    def test_metrics_use_only_prior_days(self):
        r=pre_signal_metrics("2026-10-26",self.bars)
        self.assertEqual(r["status"],"historical_context_available")
        self.assertTrue(r["signal_day_excluded"])
        self.assertGreater(r["return_5_sessions_pct"],0)

    def test_signal_day_and_future_not_leaked(self):
        start=datetime(2026,10,26,tzinfo=timezone.utc)
        self.bars.append({"timestamp":int(start.timestamp()),"open":1000,"high":2000,"low":1,"close":1000})
        r=pre_signal_metrics("2026-10-26",self.bars)
        self.assertLess(r["recovery_from_20_session_low_pct"],100)

    def test_short_history_not_fabricated(self):
        r=pre_signal_metrics("2026-10-26",self.bars[:3])
        self.assertEqual(r["status"],"insufficient_history")

if __name__=="__main__":
    unittest.main()
