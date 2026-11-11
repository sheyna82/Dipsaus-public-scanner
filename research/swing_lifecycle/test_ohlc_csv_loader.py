import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from research.swing_lifecycle.ohlc_csv_loader import load_daily_ohlc_csv


class OhlcCsvLoaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "sample.csv"

    def write_rows(self, rows):
        with self.path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["date", "open", "high", "low", "close"])
            writer.writeheader()
            writer.writerows(rows)

    def sample(self):
        return [{"date": (date(2025, 1, 1) + timedelta(days=i)).isoformat(),
                 "open": 100, "high": 101, "low": 99, "close": 100}
                for i in range(30)]

    def test_valid_rows_load_with_uncertified_provenance(self):
        self.write_rows(self.sample())
        data = load_daily_ohlc_csv(self.path, source="test-fixture", ticker="ABC")
        self.assertEqual(data["row_count"], 30)
        self.assertFalse(data["corporate_actions_verified"])
        self.assertFalse(data["fill_verified"])

    def test_rejects_unsorted_dates(self):
        rows = self.sample()
        rows[5], rows[6] = rows[6], rows[5]
        self.write_rows(rows)
        with self.assertRaisesRegex(ValueError, "nonchronological_sessions"):
            load_daily_ohlc_csv(self.path, source="fixture", ticker="ABC")

    def test_rejects_invalid_ohlc(self):
        rows = self.sample()
        rows[20]["high"] = 90
        self.write_rows(rows)
        with self.assertRaisesRegex(ValueError, "inconsistent_ohlc"):
            load_daily_ohlc_csv(self.path, source="fixture", ticker="ABC")

    def test_rejects_missing_source(self):
        self.write_rows(self.sample())
        with self.assertRaisesRegex(ValueError, "missing_data_source"):
            load_daily_ohlc_csv(self.path, source="", ticker="ABC")


if __name__ == "__main__":
    unittest.main()
