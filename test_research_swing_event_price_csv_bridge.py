import csv
import json
import tempfile
import unittest
from pathlib import Path
from research_swing_event_price_csv_bridge import (
    load_verified_price_csv, prepare_event_study_input)

COLUMNS = ["open_at", "close_at", "open", "high", "low", "close"]

def write_prices(path, *, naive=False):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        for day in (1, 2, 3):
            writer.writerow(dict(open_at=f"2020-01-{day:02d}T09:00:00" + ("" if naive else "Z"),
                                 close_at=f"2020-01-{day:02d}T17:00:00" + ("" if naive else "Z"),
                                 open=100, high=102, low=99, close=101))

class PriceCsvBridgeTests(unittest.TestCase):
    def test_load_real_csv_shape(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            write_prices(path)
            self.assertEqual(len(load_verified_price_csv(path)), 3)
    def test_timezone_naive_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            write_prices(path, naive=True)
            with self.assertRaisesRegex(ValueError, "timezone_required"):
                load_verified_price_csv(path)
    def test_prepare_multi_symbol_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            prices = root / "prices.csv"
            events = root / "events.json"
            write_prices(prices)
            events.write_text(json.dumps([]), encoding="utf-8")
            result = prepare_event_study_input(events, {"A": prices, "B": prices})
            self.assertEqual(set(result["bars_by_symbol"]), {"A", "B"})
    def test_reject_missing_column(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            path.write_text("date,open\n2020-01-01,100\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing_price_columns"):
                load_verified_price_csv(path)

if __name__ == "__main__":
    unittest.main()
