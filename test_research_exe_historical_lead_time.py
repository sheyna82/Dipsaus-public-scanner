import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from research_exe_historical_lead_time import evaluate_payload


class ExeHistoricalDiagnosticTests(unittest.TestCase):
    def test_missing_minute_reported_before_replay(self):
        start = datetime(2026, 10, 21, 9, 30, tzinfo=ZoneInfo("America/New_York"))
        stamps = [int((start + timedelta(minutes=i)).timestamp())
                  for i in range(390) if i != 17]
        n = len(stamps)
        quote = {"open": [100.] * n, "high": [101.] * n,
                 "low": [99.] * n, "close": [100.] * n}
        payload = {"chart": {"result": [{"timestamp": stamps,
                                         "indicators": {"quote": [quote]}}]}}
        result = evaluate_payload(payload)
        self.assertEqual(result["status"], "DATA_BLOCKED")
        self.assertEqual(result["reason"], "incomplete_regular_session")
        self.assertEqual(result["minute_audit"]["missing_count"], 1)
        self.assertIn("09:47:00", result["minute_audit"]["missing_minutes_ny"][0])


    def test_null_ohlc_reports_exact_minute(self):
        start = datetime(2026, 10, 21, 9, 30, tzinfo=ZoneInfo("America/New_York"))
        stamps = [int((start + timedelta(minutes=i)).timestamp()) for i in range(390)]
        quote = {"open": [100.] * 390, "high": [101.] * 390,
                 "low": [99.] * 390, "close": [100.] * 390}
        quote["close"][17] = None
        payload = {"chart": {"result": [{"timestamp": stamps,
                                         "indicators": {"quote": [quote]}}]}}
        result = evaluate_payload(payload)
        self.assertEqual(result["reason"], "missing_or_invalid_ohlc")
        self.assertEqual(result["invalid_ohlc_count"], 1)
        self.assertIn("09:47:00", result["invalid_ohlc_minutes_ny"][0])


if __name__ == "__main__":
    unittest.main()
