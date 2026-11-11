"""Contract tests for leakage-safe pre-entry stock regimes."""
import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from research.swing_lifecycle.warning_preentry_regimes import evaluate


class PreentryRegimesTests(unittest.TestCase):
    def test_ignores_entry_day_and_future_bars(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bars = []
            for i in range(24):
                price = 100.0 if i < 21 else 1000.0
                bars.append([f"2026-01-{i+1:02d}", price, price + 1, price - 1, price, 100])
            archive = root / "bars.jsonl.gz"
            with gzip.open(archive, "wt") as f:
                f.write(json.dumps({"symbol": "TEST", "bars": bars}) + "\n")
            cases = root / "cases.csv"
            with cases.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "ticker", "entry_date", "confirmation_sessions", "return_difference_pp",
                    "candidate_mae_pct", "baseline_mae_pct", "early_exit"])
                writer.writeheader()
                writer.writerow({"ticker": "TEST", "entry_date": bars[20][0],
                                 "confirmation_sessions": 1, "return_difference_pp": 2,
                                 "candidate_mae_pct": -1, "baseline_mae_pct": -4,
                                 "early_exit": "True"})
            result = evaluate(cases, archive)
            self.assertEqual(result["counts"]["rows"], 1)
            self.assertEqual(result["groups"][0]["trend"], "positive")
            self.assertEqual(result["groups"][0]["volatility"], "low_range")
            self.assertEqual(result["groups"][0]["early_exits"], 1)
            self.assertEqual(result["groups"][0]["mean_mae_improvement_pp"], 3)


if __name__ == "__main__":
    unittest.main()
