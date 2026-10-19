import unittest
from datetime import datetime, timezone
from dipsaus_eu_session_context import eu_session_context

class TestEUSessionContext(unittest.TestCase):
    def test_evening(self):
        self.assertEqual(eu_session_context(datetime(2026,10,19,20,36,tzinfo=timezone.utc)),"OUTSIDE_CORE_HOURS")
    def test_core(self):
        self.assertEqual(eu_session_context(datetime(2026,10,19,10,tzinfo=timezone.utc)),"CORE_HOURS_UNVERIFIED_HOLIDAYS")
    def test_weekend(self):
        self.assertEqual(eu_session_context(datetime(2026,10,18,10,tzinfo=timezone.utc)),"WEEKEND_CLOSED")
    def test_naive_unknown(self):
        self.assertEqual(eu_session_context(datetime(2026,10,19,10)),"UNKNOWN")
    def test_summer_dst(self):
        self.assertEqual(eu_session_context(datetime(2026,7,20,15,40,tzinfo=timezone.utc)),"OUTSIDE_CORE_HOURS")
if __name__=="__main__": unittest.main()
