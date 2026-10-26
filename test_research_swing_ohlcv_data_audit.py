"""Synthetic tests for historical OHLCV data audit."""
import unittest
from datetime import date, timedelta
from research_swing_ohlcv_data_audit import validate_daily_ohlcv_bars


def bars():
    return [{"session_date": (date(2026, 9, 1) + timedelta(days=i)).isoformat(),
             "open": 100, "high": 105, "low": 95, "close": 101,
             "volume": 10000} for i in range(15)]


class OHLCVDataAuditTests(unittest.TestCase):
    def test_valid_synthetic_bars(self):
        result = validate_daily_ohlcv_bars(bars())
        self.assertEqual(result["validated_sessions"], 15)
        self.assertFalse(result["source_authenticity_verified"])

    def test_insufficient_history_rejected(self):
        with self.assertRaisesRegex(ValueError, "insufficient_market_history"):
            validate_daily_ohlcv_bars(bars()[:10])

    def test_duplicate_session_rejected(self):
        x = bars()
        x[2]["session_date"] = x[1]["session_date"]
        with self.assertRaisesRegex(ValueError, "duplicate_or_unsorted_session"):
            validate_daily_ohlcv_bars(x)

    def test_inconsistent_high_low_rejected(self):
        x = bars()
        x[0]["high"] = 99
        with self.assertRaisesRegex(ValueError, "inconsistent_ohlc"):
            validate_daily_ohlcv_bars(x)

    def test_zero_volume_rejected(self):
        x = bars()
        x[0]["volume"] = 0
        with self.assertRaisesRegex(ValueError, "invalid_volume"):
            validate_daily_ohlcv_bars(x)

    def test_nan_price_rejected(self):
        x = bars()
        x[0]["close"] = "NaN"
        with self.assertRaisesRegex(ValueError, "invalid_market_number"):
            validate_daily_ohlcv_bars(x)

    def test_unsorted_sessions_rejected(self):
        x = bars()
        x[2]["session_date"] = "2026-08-31"
        with self.assertRaisesRegex(ValueError, "duplicate_or_unsorted_session"):
            validate_daily_ohlcv_bars(x)


if __name__ == "__main__":
    unittest.main()
