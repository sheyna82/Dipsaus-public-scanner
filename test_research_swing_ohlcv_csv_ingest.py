"""Tests for reproducible OHLCV CSV import."""
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from research_swing_ohlcv_csv_ingest import load_verified_ohlcv_csv


def csv_content():
    lines = ["session_date,open,high,low,close,volume"]
    for i in range(15):
        day = (date(2026, 9, 1) + timedelta(days=i)).isoformat()
        lines.append(f"{day},100,105,95,101,10000")
    return "\n".join(lines) + "\n"


class CSVIngestTests(unittest.TestCase):
    def load(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prices.csv"
            path.write_text(content, encoding="utf-8")
            return load_verified_ohlcv_csv(path)

    def test_valid_import_and_hash(self):
        result = self.load(csv_content())
        self.assertEqual(result["bar_count"], 15)
        self.assertEqual(len(result["sha256"]), 64)
        self.assertFalse(result["provider_identity_verified"])

    def test_bad_header_rejected(self):
        with self.assertRaisesRegex(ValueError, "unexpected_ohlcv_columns"):
            self.load(csv_content().replace("session_date,open", "date,open"))

    def test_extra_column_rejected(self):
        with self.assertRaisesRegex(ValueError, "malformed_ohlcv_row"):
            self.load(csv_content().replace(",10000\n", ",10000,extra\n", 1))

    def test_duplicate_session_rejected(self):
        rows = csv_content().splitlines()
        rows[3] = rows[2]
        with self.assertRaisesRegex(ValueError, "duplicate_or_unsorted_session"):
            self.load("\n".join(rows) + "\n")


if __name__ == "__main__":
    unittest.main()
