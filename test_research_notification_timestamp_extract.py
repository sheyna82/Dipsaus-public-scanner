import unittest
from research_notification_timestamp_extract import verified_notification_times
class TimestampTests(unittest.TestCase):
    def test_extract_only_selected_symbols_and_utc(self):
        state={"signals":{"US-EARLY|VIST|2026-10-26":{"notified_utc":"2026-10-26T13:51:00+01:00","delivery":"sent","secret":"DO_NOT_LEAK"},"ENTRY|US|FANG|PHASE":{"notified_utc":"2026-10-26T13:46:00Z"},"EXIT|EXE|STATE":{"notified_utc":"invalid"}}}
        r=verified_notification_times(state,["VIST"])
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]["notification_utc"],"2026-10-26T12:51:00+00:00")
        self.assertNotIn("secret",str(r))
        self.assertFalse(r[0]["execution_verified"])
    def test_naive_timestamp_not_verified(self):
        self.assertEqual(verified_notification_times({"signals":{"US-EARLY|VIST|2026-10-26":{"notified_utc":"2026-10-26T13:51:00"}}},["VIST"]),[])
if __name__=="__main__":unittest.main()
