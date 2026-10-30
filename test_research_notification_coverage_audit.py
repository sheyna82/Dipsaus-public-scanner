import unittest
from datetime import datetime,timezone,timedelta
from research_notification_signal_cases import CASES_2026_10_26
from research_notification_coverage_audit import audit_coverage

class CoverageTests(unittest.TestCase):
    def test_no_utc_timestamp_fabrication(self):
        result=audit_coverage(CASES_2026_10_26,{})
        self.assertEqual(len(result),8)
        self.assertTrue(all(not x["verified_signal_utc"] for x in result))
        self.assertTrue(all(not x["ready_for_forward_return"] for x in result))

    def test_historical_coverage_without_forward_claim(self):
        base=datetime(2026,9,1,tzinfo=timezone.utc)
        bars=[dict(timestamp=int((base+timedelta(days=i)).timestamp()),open=100,high=110,low=90,close=101) for i in range(40)]
        result=audit_coverage(CASES_2026_10_26,{"EXE":{"bars":bars}})
        self.assertTrue(result[0]["ready_for_pre_signal_context"])
        self.assertFalse(result[0]["ready_for_forward_return"])

    def test_reject_duplicate_daily_dates(self):
        b={"timestamp":int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp()),"open":1,"high":2,"low":1,"close":2}
        result=audit_coverage(CASES_2026_10_26,{"EXE":{"bars":[b,b]}})
        self.assertEqual(result[0]["status"],"duplicate_or_unsorted_dates")

if __name__=="__main__":
    unittest.main()
