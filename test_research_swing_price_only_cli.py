import csv
import tempfile
import unittest
from pathlib import Path
from research_swing_price_only_cli import run_price_csv_study

class PriceOnlyCliTests(unittest.TestCase):
    def test_real_csv_ingestion_has_sha256_and_returns(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["open_at", "close_at", "open", "high", "low", "close"])
                for i in range(1, 29):
                    close = 100 if i < 12 else 85 + (i - 12)
                    writer.writerow([f"2026-01-{i:02d}T09:30:00Z",
                                     f"2026-01-{i:02d}T16:00:00Z",
                                     close, close + 1, close - 1, close])
            result = run_price_csv_study({"SAMPLE": path}, horizons=(3,), lookback=5)
            self.assertEqual(result["sources"]["SAMPLE"]["bar_count"], 28)
            self.assertEqual(len(result["sources"]["SAMPLE"]["sha256"]), 64)
            self.assertGreater(result["horizons"]["3"]["baseline_observations_overlapping"], 0)
            self.assertFalse(result["predictive_edge_proven"])
    def test_missing_csv_fails(self):
        with self.assertRaises(FileNotFoundError):
            run_price_csv_study({"X": "/nonexistent/dipsaus.csv"})

if __name__ == "__main__":
    unittest.main()
