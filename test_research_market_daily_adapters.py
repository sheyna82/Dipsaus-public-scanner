"""Offline synthetic vendor adapter tests."""
import unittest
from research_market_daily_adapters import parse_tiingo_daily, parse_twelve_data_daily, parse_alpha_vantage_daily, parse_finnhub_candles, parse_massive_daily_aggregates, parse_alpaca_daily_bars


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

    def test_alpha_vantage_daily_raw_and_quota_failure(self):
        payload = {"Time Series (Daily)": {
            "2026-10-22": {"4. close": "102.5"},
            "2026-10-21": {"4. close": "100.0"}}}
        self.assertEqual(parse_alpha_vantage_daily(payload)[0]["close"], "100.0")
        with self.assertRaisesRegex(ValueError, "vendor_error"):
            parse_alpha_vantage_daily({"Note": "API call frequency limit"})
        with self.assertRaisesRegex(ValueError, "invalid_daily_record"):
            parse_alpha_vantage_daily({"Time Series (Daily)": {
                "2026-10-21": {"4. close": None}}})

    def test_finnhub_candles_and_missing_entitlement(self):
        from datetime import datetime, timezone
        def ts(day):
            return int(datetime(2026, 10, day, tzinfo=timezone.utc).timestamp())
        result = parse_finnhub_candles({"s": "ok", "t": [ts(22), ts(21)],
                                         "c": [102, 100]})
        self.assertEqual(result[0], {"date": "2026-10-21", "close": "100"})
        with self.assertRaisesRegex(ValueError, "vendor_error"):
            parse_finnhub_candles({"s": "no_data"})
        with self.assertRaisesRegex(ValueError, "invalid_candle_arrays"):
            parse_finnhub_candles({"s": "ok", "t": [ts(21)], "c": []})
        with self.assertRaisesRegex(ValueError, "invalid_candle_timestamp"):
            parse_finnhub_candles({"s": "ok", "t": [True], "c": [100]})

    def test_massive_adjustment_mode_and_millisecond_timestamps(self):
        from datetime import datetime, timezone
        def millis(day):
            return int(datetime(2026, 10, day, tzinfo=timezone.utc).timestamp() * 1000)
        payload = {"status": "OK", "adjusted": True,
                   "results": [{"t": millis(22), "c": 102},
                               {"t": millis(21), "c": 100}]}
        self.assertEqual(parse_massive_daily_aggregates(payload, adjusted=True)[0],
                         {"date": "2026-10-21", "close": "100"})
        with self.assertRaisesRegex(ValueError, "adjustment_mode_mismatch"):
            parse_massive_daily_aggregates(payload, adjusted=False)
        with self.assertRaisesRegex(ValueError, "vendor_error"):
            parse_massive_daily_aggregates({"status": "NOT_AUTHORIZED"}, adjusted=True)
        with self.assertRaisesRegex(ValueError, "invalid_candle_timestamp"):
            parse_massive_daily_aggregates({"status": "OK", "adjusted": True,
                                            "results": [{"t": True, "c": 100}]},
                                           adjusted=True)

    def test_alpaca_bars_and_missing_symbol(self):
        payload = {"bars": {"AMD": [
            {"t": "2026-10-22T00:00:00Z", "c": 102},
            {"t": "2026-10-21T00:00:00Z", "c": 100}]}}
        self.assertEqual(parse_alpaca_daily_bars(payload, symbol="AMD")[0],
                         {"date": "2026-10-21", "close": "100"})
        with self.assertRaisesRegex(ValueError, "missing_daily_prices"):
            parse_alpaca_daily_bars(payload, symbol="TSLA")
        with self.assertRaisesRegex(ValueError, "symbol_required"):
            parse_alpaca_daily_bars(payload, symbol="")

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
