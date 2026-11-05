import unittest
from datetime import datetime, timezone, timedelta
from research_notification_case_report import case_report

class CaseReportTests(unittest.TestCase):
    def setUp(self):
        self.t=datetime(2026,10,26,12,0,tzinfo=timezone.utc)
        base=datetime(2026,10,1,tzinfo=timezone.utc)
        self.bars=[{"timestamp":int((base+timedelta(days=i)).timestamp()),"open":100,"high":110,"low":90,"close":101} for i in range(50)]

    def test_missing_benchmark_not_invented(self):
        r=case_report("EXE",self.t,self.bars)
        self.assertIsNone(r["benchmark_relative"][3])
        self.assertFalse(r["trade_ready"])

    def test_signal_day_not_used_for_pre_signal(self):
        r=case_report("EXE",self.t,self.bars)
        self.assertLess(r["pre_signal"]["last_bar_timestamp"],int(datetime(2026,10,26,tzinfo=timezone.utc).timestamp()))

    def test_no_naive_timestamp(self):
        with self.assertRaises(ValueError):
            case_report("EXE",datetime(2026,10,26),self.bars)

if __name__=="__main__":
    unittest.main()
