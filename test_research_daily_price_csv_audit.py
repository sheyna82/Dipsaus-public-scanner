"""Offline price-bar audit regression tests; fixtures are synthetic."""
import unittest

from research_daily_price_csv_audit import audit_daily_price_csv

HEADER = b"date,open,high,low,close,volume\n"
ROW = b"2026-01-02,10,12,9,11,100\n"


class PriceCsvAuditTests(unittest.TestCase):
    def test_valid_synthetic_prices_not_verified(self):
        result = audit_daily_price_csv(HEADER + ROW)
        self.assertEqual(result["rows"], 1)
        self.assertFalse(result["point_in_time_verified"])
        self.assertFalse(result["trade_ready"])

    def test_duplicate_date_rejected(self):
        with self.assertRaisesRegex(ValueError, "unordered_or_duplicate_dates"):
            audit_daily_price_csv(HEADER + ROW + ROW)

    def test_inconsistent_ohlc_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_ohlcv"):
            audit_daily_price_csv(HEADER + b"2026-01-02,10,9,8,11,100\n")

    def test_negative_volume_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_ohlcv"):
            audit_daily_price_csv(HEADER + b"2026-01-02,10,12,9,11,-1\n")

    def test_unexpected_columns_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_columns"):
            audit_daily_price_csv(b"ticker," + HEADER + ROW)


if __name__ == "__main__":
    unittest.main()
