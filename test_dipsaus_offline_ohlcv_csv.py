import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta
from dipsaus_offline_ohlcv_csv import load_local_ohlcv_csv
from dipsaus_offline_ohlcv_features import calculate_recovery_features


def csv_rows():
    start = date(2026, 9, 1)
    lines = ["Date,Open,High,Low,Close,Volume"]
    for i in range(23):
        lines.append(f"{(start + timedelta(days=i)).isoformat()},{100+i},{101+i},{99+i},{100+i},1000")
    return "\n".join(lines) + "\n"


class CsvTests(unittest.TestCase):
    def test_csv_to_features(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bars.csv"
            path.write_text(csv_rows(), encoding="utf-8")
            bars = load_local_ohlcv_csv(path)
            self.assertEqual(len(bars), 23)
            self.assertIsNotNone(calculate_recovery_features(bars, bars, 12))

    def test_rejects_duplicate_dates(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bars.csv"
            lines = csv_rows().splitlines()
            lines[-1] = lines[-2]
            path.write_text("\n".join(lines), encoding="utf-8")
            self.assertIsNone(load_local_ohlcv_csv(path))

    def test_rejects_wrong_header_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bars.csv"
            path.write_text(csv_rows().replace("Date,Open", "Date,Price"), encoding="utf-8")
            self.assertIsNone(load_local_ohlcv_csv(path))
            path.write_text(csv_rows().replace(",1000", ",NaN", 1), encoding="utf-8")
            self.assertIsNone(load_local_ohlcv_csv(path))

    def test_rejects_html_challenge(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bars.csv"
            path.write_text("<html>Rate limit</html>", encoding="utf-8")
            self.assertIsNone(load_local_ohlcv_csv(path))


if __name__ == "__main__":
    unittest.main()
