import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from dipsaus_offline_benchmark_sessions import check_benchmark_sessions


def make_rows(count=30, offset=0):
    start = date(2025, 1, 1) + timedelta(days=offset)
    lines = ["Date,Open,High,Low,Close,Volume"]
    for i in range(count):
        d = (start + timedelta(days=i)).isoformat()
        lines.append(f"{d},100,101,99,100,1000")
    return "\n".join(lines) + "\n"


class BenchmarkSessionsTests(unittest.TestCase):
    def test_exact_alignment(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "stock.csv", Path(folder) / "benchmark.csv"
            a.write_text(make_rows(), encoding="utf-8")
            b.write_text(make_rows(), encoding="utf-8")
            result = check_benchmark_sessions(a, b)
            self.assertTrue(result["exact_alignment"])
            self.assertEqual(result["shared_sessions"], 30)
            self.assertFalse(result["trade_ready"])

    def test_missing_sessions_are_visible(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "stock.csv", Path(folder) / "benchmark.csv"
            a.write_text(make_rows(), encoding="utf-8")
            b.write_text(make_rows(offset=2), encoding="utf-8")
            result = check_benchmark_sessions(a, b)
            self.assertFalse(result["exact_alignment"])
            self.assertEqual(result["missing_benchmark_sessions"], 2)
            self.assertEqual(result["missing_stock_sessions"], 2)

    def test_rejects_unusable_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "stock.csv", Path(folder) / "benchmark.csv"
            a.write_text("not a csv", encoding="utf-8")
            b.write_text(make_rows(), encoding="utf-8")
            self.assertEqual(check_benchmark_sessions(a, b)["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
