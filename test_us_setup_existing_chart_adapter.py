import unittest
from datetime import datetime, timedelta, timezone
from research.us_setup_existing_chart_adapter import adapt_us_chart_rows


class ExistingUSChartAdapterTests(unittest.TestCase):
    def setUp(self):
        start = datetime(2026, 10, 1, 14, 30, tzinfo=timezone.utc)
        self.rows = [{"ts": (start + timedelta(minutes=5*i)).timestamp(),
                      "low": 99, "close": 100} for i in range(25)]

    def test_existing_chart_schema_accepted(self):
        result = adapt_us_chart_rows(self.rows)
        self.assertTrue(result["usable"])
        self.assertEqual(result["interval_minutes"], 5)
        self.assertFalse(result["provider_verified"])

    def test_wrong_interval_rejected(self):
        self.assertEqual(adapt_us_chart_rows(self.rows, expected_interval_minutes=15)["reason"],
                         "INTERVAL_NOT_VERIFIED")

    def test_daily_bars_rejected(self):
        rows = list(self.rows)
        start = datetime(2026, 10, 1, tzinfo=timezone.utc)
        for i, row in enumerate(rows):
            row["ts"] = (start + timedelta(days=i)).timestamp()
        self.assertFalse(adapt_us_chart_rows(rows)["usable"])

    def test_missing_timestamp_rejected(self):
        rows = list(self.rows)
        rows[4] = {"low": 99, "close": 100}
        self.assertEqual(adapt_us_chart_rows(rows)["reason"], "MISSING_SOURCE_TIMESTAMP")

    def test_no_network_or_live_promotion(self):
        result = adapt_us_chart_rows(self.rows)
        self.assertTrue(result["research_only"])
        self.assertFalse(result["provider_verified"])


if __name__ == "__main__":
    unittest.main()
