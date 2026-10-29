"""Regression tests for research-only duration placebo."""
import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from research.swing_lifecycle.warning_duration_placebo import evaluate


class DurationPlaceboTests(unittest.TestCase):
    def make_inputs(self, folder, *, train_warning=True):
        archive = Path(folder) / "bars.jsonl.gz"
        cases = Path(folder) / "cases.csv"
        bars = []
        from datetime import date, timedelta
        day = date(2025, 11, 1)
        while day <= date(2026, 3, 31):
            if day.weekday() < 5:
                bars.append([day.isoformat(), 100.0, 101.0, 99.0, 100.0, 1000])
            day += timedelta(days=1)
        with gzip.open(archive, "wt", encoding="utf-8") as stream:
            stream.write(json.dumps({"symbol": "TEST", "bars": bars}) + "\n")
        dates = [bar[0] for bar in bars]
        train = dates.index("2025-11-10")
        test = dates.index("2026-02-02")
        fields = ["ticker", "entry_date", "exit_date", "confirmation_sessions",
                  "early_exit", "return_difference_pp", "baseline_mae_pct"]
        with cases.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerow(dict(ticker="TEST", entry_date=dates[train],
                exit_date=dates[train + (3 if train_warning else 10)],
                confirmation_sessions=1, early_exit=str(train_warning),
                return_difference_pp=0, baseline_mae_pct=-1))
            writer.writerow(dict(ticker="TEST", entry_date=dates[test],
                exit_date=dates[test + 4], confirmation_sessions=1,
                early_exit="True", return_difference_pp=0, baseline_mae_pct=-1))
        return cases, archive

    def test_reproducible_and_training_only(self):
        with tempfile.TemporaryDirectory() as folder:
            cases, archive = self.make_inputs(folder)
            first = evaluate(cases, archive)
            self.assertEqual(first, evaluate(cases, archive))
            self.assertEqual(first["test_candidates"], 1)
            self.assertEqual(first["training_duration_counts"], {3: 1})
            self.assertEqual(first["rows"][0]["placebo_duration"], 3)
            self.assertFalse(first["trade_ready"])

    def test_no_training_warning_is_error(self):
        with tempfile.TemporaryDirectory() as folder:
            cases, archive = self.make_inputs(folder, train_warning=False)
            with self.assertRaisesRegex(ValueError, "no_training_warning_durations"):
                evaluate(cases, archive)


if __name__ == "__main__":
    unittest.main()
