import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from dipsaus_offline_csv_pilot import score_local_csv_pair


def rows():
    first = date(2026, 9, 1)
    data = ["Date,Open,High,Low,Close,Volume"]
    for i in range(23):
        data.append(f"{(first + timedelta(days=i)).isoformat()},{100+i},{101+i},{99+i},{100+i},1000")
    return "\n".join(data) + "\n"


class CsvPilotTests(unittest.TestCase):
    def test_end_to_end_research_score(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "stock.csv", Path(folder) / "market.csv"
            a.write_text(rows(), encoding="utf-8")
            b.write_text(rows(), encoding="utf-8")
            result = score_local_csv_pair(a, b, days_to_earnings=12)
            self.assertEqual(result["status"], "RESEARCH_ONLY")
            self.assertEqual(result["signal_date"], "2026-09-23")
            self.assertIsNotNone(result["baseline"]["score"])
            self.assertFalse(result["trade_ready"])
            self.assertFalse(result["source_verified"])

    def test_rejects_bad_file(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "stock.csv", Path(folder) / "market.csv"
            a.write_text("<html>Access denied</html>", encoding="utf-8")
            b.write_text(rows(), encoding="utf-8")
            self.assertEqual(score_local_csv_pair(a, b, days_to_earnings=12)["status"], "REJECTED")

    def test_requires_earnings_distance(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "stock.csv", Path(folder) / "market.csv"
            a.write_text(rows(), encoding="utf-8")
            b.write_text(rows(), encoding="utf-8")
            self.assertEqual(score_local_csv_pair(a, b, days_to_earnings=None)["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
