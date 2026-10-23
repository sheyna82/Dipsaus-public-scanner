"""Synthetic-only tests for Kaggle schema conversion."""
import unittest

from research_kaggle_daily_converter import convert_kaggle_daily_csv

HEADER = b"Date,Open,High,Low,Close,Volume,OpenInt\n"


class KaggleConverterTests(unittest.TestCase):
    def test_converts_and_audits(self):
        data = HEADER + b"2017-01-03,10,12,9,11,1000,0\n"
        result = convert_kaggle_daily_csv(data)
        self.assertEqual(result, b"date,open,high,low,close,volume\n2017-01-03,10,12,9,11,1000\n")

    def test_rejects_extra_column(self):
        with self.assertRaisesRegex(ValueError, "invalid_kaggle_columns"):
            convert_kaggle_daily_csv(b"Date,Open,High,Low,Close,Volume,OpenInt,Extra\n")

    def test_rejects_invalid_open_interest(self):
        with self.assertRaisesRegex(ValueError, "invalid_open_interest"):
            convert_kaggle_daily_csv(HEADER + b"2017-01-03,10,12,9,11,1000,not-a-number\n")

    def test_rejects_invalid_prices(self):
        with self.assertRaisesRegex(ValueError, "invalid_ohlcv"):
            convert_kaggle_daily_csv(HEADER + b"2017-01-03,10,8,9,11,1000,0\n")

    def test_rejects_duplicate_dates(self):
        with self.assertRaisesRegex(ValueError, "unordered_or_duplicate_dates"):
            convert_kaggle_daily_csv(HEADER + b"2017-01-03,10,12,9,11,1000,0\n2017-01-03,10,12,9,11,1000,0\n")


if __name__ == "__main__":
    unittest.main()
