import unittest
from datetime import datetime, timezone, timedelta
from dipsaus_eu_freshness import classify_eu_report

class TestEUFreshness(unittest.TestCase):
    def setUp(self): self.now=datetime(2026,10,19,20,tzinfo=timezone.utc)
    def test_fresh(self):
        self.assertTrue(classify_eu_report({"generated_utc":self.now.isoformat()},self.now)["fresh"])
    def test_expired(self):
        self.assertEqual(classify_eu_report({"generated_utc":(self.now-timedelta(minutes=26)).isoformat()},self.now)["reason"],"EXPIRED_REPORT")
    def test_future(self):
        self.assertEqual(classify_eu_report({"generated_utc":(self.now+timedelta(minutes=1)).isoformat()},self.now)["reason"],"FUTURE_TIMESTAMP")
    def test_missing(self):
        self.assertFalse(classify_eu_report({},self.now)["fresh"])
    def test_naive(self):
        self.assertEqual(classify_eu_report({"generated_utc":self.now.replace(tzinfo=None).isoformat()},self.now)["reason"],"INVALID_TIMESTAMP")
if __name__=="__main__": unittest.main()
