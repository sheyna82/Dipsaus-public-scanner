import unittest
from datetime import datetime,timezone,timedelta
from research_notification_outcome_readiness import outcome_readiness
class ReadinessTests(unittest.TestCase):
    def bar(self,day):
        return {"timestamp":int(datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())}
    def test_no_future_sessions(self):
        r=outcome_readiness("2026-10-26",[self.bar("2026-10-23"),self.bar("2026-10-26")])
        self.assertEqual(r["observed_subsequent_sessions"],0)
        self.assertFalse(r["horizons"]["3"]["ready"])
    def test_actual_sessions_not_calendar_days(self):
        r=outcome_readiness("2026-10-26",[self.bar("2026-10-27"),self.bar("2026-10-29"),self.bar("2026-11-02")])
        self.assertTrue(r["horizons"]["3"]["ready"])
        self.assertEqual(r["horizons"]["3"]["earliest_exit_session"],"2026-11-02")
        self.assertFalse(r["horizons"]["5"]["ready"])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            outcome_readiness("2026-10-26",[self.bar("2026-10-27")]*2)
if __name__=="__main__":unittest.main()
