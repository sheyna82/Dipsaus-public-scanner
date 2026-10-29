import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from research.swing_lifecycle.run_historical_csv_benchmark import run_historical_csv_benchmark


class HistoricalCsvBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def make_data(self, ticker, start):
        path = self.folder / (ticker + ".csv")
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["date", "open", "high", "low", "close"])
            writer.writeheader()
            for i in range(32):
                d = start + timedelta(days=i)
                bar = {"date": d.isoformat(), "open": 100,
                       "high": 101, "low": 99, "close": 100}
                if i == 24:
                    bar.update(open=94, high=95, low=90, close=91)
                if i == 25:
                    bar.update(open=89, high=91, low=88, close=90)
                writer.writerow(bar)
        return {"ticker": ticker, "csv_path": path.name,
                "entry_date": (start + timedelta(days=21)).isoformat(),
                "baseline_exit_date": (start + timedelta(days=29)).isoformat(),
                "score": "10"}

    def manifest(self, records):
        path = self.folder / "manifest.csv"
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=[
                "ticker", "csv_path", "entry_date", "baseline_exit_date", "score"])
            writer.writeheader()
            writer.writerows(records)
        return path

    def test_end_to_end_csv_holdout(self):
        old = self.make_data("OLD", date(2025, 1, 1))
        new = self.make_data("NEW", date(2026, 1, 1))
        result = run_historical_csv_benchmark(
            self.manifest([old, new]), cutoff=date(2025, 8, 1),
            source="unit-test-fixture")
        self.assertEqual(result["trade_candidates_supplied"], 2)
        self.assertEqual(result["unique_tickers"], 2)
        self.assertEqual(result["training"]["trade_candidates"], 1)
        self.assertEqual(result["holdout"]["trade_candidates"], 1)
        self.assertFalse(result["historical_edge_proven"])
        self.assertFalse(result["candidate_selection_independently_verified"])

    def test_manifest_non_session_date_rejected(self):
        record = self.make_data("OLD", date(2025, 1, 1))
        record["entry_date"] = "2024-01-01"
        with self.assertRaisesRegex(ValueError, "manifest_date_not_a_session"):
            run_historical_csv_benchmark(
                self.manifest([record]), cutoff=date(2025, 8, 1),
                source="fixture")


if __name__ == "__main__":
    unittest.main()
