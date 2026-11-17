import unittest
from research.us_session_sanity_20261117 import review_us_session

class SessionSanityTests(unittest.TestCase):
    def review(self,stamp,date,**kw):
        return review_us_session(observation_utc=stamp,claimed_session_date=date,**kw)
    def test_regular_tuesday_remains_unverified(self):
        x=self.review("2026-11-17T15:30:00Z","2026-11-17")
        self.assertEqual(x["blocks"],["OFFICIAL_EXCHANGE_CALENDAR_UNVERIFIED"])
        self.assertFalse(x["trade_ready"])
    def test_weekend_rejected(self):
        x=self.review("2026-11-14T16:00:00Z","2026-11-14")
        self.assertIn("WEEKEND_NOT_REGULAR_SESSION",x["blocks"])
    def test_utc_midnight_is_previous_new_york_date(self):
        x=self.review("2026-11-18T00:15:00Z","2026-11-17")
        self.assertNotIn("NEW_YORK_SESSION_DATE_MISMATCH",x["blocks"])
    def test_wrong_local_date_rejected(self):
        x=self.review("2026-11-18T00:15:00Z","2026-11-18")
        self.assertIn("NEW_YORK_SESSION_DATE_MISMATCH",x["blocks"])
    def test_naive_time_rejected(self):
        x=self.review("2026-11-17T15:30:00","2026-11-17")
        self.assertIn("OBSERVATION_TIME_UNRESOLVED",x["blocks"])
    def test_bad_calendar_date_rejected(self):
        x=self.review("2026-11-17T15:30:00Z","2026-02-30")
        self.assertIn("SESSION_DATE_UNRESOLVED",x["blocks"])
    def test_self_attested_calendar_never_authorizes(self):
        x=self.review("2026-11-17T15:30:00Z","2026-11-17",official_calendar_verified=True)
        self.assertFalse(x["calendar_verified"])
        self.assertFalse(x["notify"])
if __name__=="__main__":
    unittest.main()
