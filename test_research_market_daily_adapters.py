"""Offline synthetic vendor adapter tests."""
import unittest
from research_market_daily_adapters import parse_tiingo_daily, parse_twelve_data_daily


class VendorAdapterTests(unittest.TestCase):
    def test_tiingo_raw_vs_adjusted_explicit(self):
        sample = [
            {"date": "2026-10-22T00:00:00Z", "close": 101, "adjClose": 99},
            {"date": "2026-10-21T00:00:00Z", "close": 100, "adjClose": 98},
        ]
        self.assertEqual([x["date"] for x in parse_tiingo_daily(sample)],
                         ["2026-10-21", "2026-10-22"])
        self.assertEqual(parse_tiingo_daily(sample, adjusted=True)[0]["close"], "98")

    def test_twelve_data_descending_json(self):
        payload = {"status": "ok", "values": [
            {"datetime": "2026-10-22", "close": "102"},
            {"datetime": "2026-10-21", "close": "100"}]}
        self.assertEqual(parse_twelve_data_daily(payload)[0]["close"], "100")

    def test_fail_closed_on_error_and_duplicate(self):
        with self.assertRaisesRegex(ValueError, "vendor_error"):
            parse_twelve_data_daily({"status": "error", "message": "quota"})
        with self.assertRaisesRegex(ValueError, "duplicate_daily_session"):
            parse_tiingo_daily([
                {"date": "2026-10-21", "close": 100},
                {"date": "2026-10-21", "close": 101}])
        with self.assertRaisesRegex(ValueError, "invalid_daily_record"):
            parse_twelve_data_daily({"values": [{"datetime": "2026-10-21", "close": "NaN"}]})


if __name__ == "__main__":
    unittest.main()
