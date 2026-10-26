import unittest
from datetime import datetime, timezone
from research_notification_pre_signal import pre_signal_context

class PreSignalTests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)
        base = int(self.t.timestamp())
        self.bars = [{"timestamp":base - (i+1)*86400, "open":100, "high":110, "low":90, "close":100} for i in range(20)]

    def test_historical_context(self):
        r=pre_signal_context(self.t,self.bars)
        self.assertEqual(r["observed_bars"],20)
        self.assertFalse(r["intraday_at_signal_known"])

    def test_future_bar_excluded(self):
        self.bars.append({"timestamp":int(self.t.timestamp())+100,"open":100,"high":999,"low":1,"close":500})
        self.assertEqual(pre_signal_context(self.t,self.bars)["lookback_high"],110)

    def test_missing_history_not_imputed(self):
        self.assertIsNone(pre_signal_context(self.t,self.bars[:2]))

if __name__=="__main__":
    unittest.main()
