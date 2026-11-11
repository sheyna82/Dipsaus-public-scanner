"""Regression checks for exchange-local daily bar dates (offline, no network)."""
import datetime as dt
import unittest
from zoneinfo import ZoneInfo

class ExchangeLocalDateTests(unittest.TestCase):
    def test_asian_session_can_be_next_calendar_day(self):
        stamp=int(dt.datetime(2026,10,26,23,30,tzinfo=dt.timezone.utc).timestamp())
        tokyo=dt.datetime.fromtimestamp(stamp,dt.timezone.utc).astimezone(ZoneInfo("Asia/Tokyo")).date()
        new_york=dt.datetime.fromtimestamp(stamp,dt.timezone.utc).astimezone(ZoneInfo("America/New_York")).date()
        self.assertEqual(tokyo.isoformat(),"2026-10-27")
        self.assertEqual(new_york.isoformat(),"2026-10-26")
        self.assertNotEqual(tokyo,new_york)

    def test_dst_exchange_local_conversion(self):
        stamp=int(dt.datetime(2026,3,30,0,30,tzinfo=dt.timezone.utc).timestamp())
        self.assertEqual(dt.datetime.fromtimestamp(stamp,dt.timezone.utc).astimezone(ZoneInfo("Europe/Amsterdam")).date().isoformat(),"2026-03-30")

if __name__=="__main__":
    unittest.main()
