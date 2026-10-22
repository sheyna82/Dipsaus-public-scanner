"""Unit tests for replay timestamp semantics and strict session integrity."""
import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from research_exe_intraday_replay import load_session
from portfolio_downside_research import replay_intraday


class ExeReplayTimestampTests(unittest.TestCase):
    def test_signal_uses_closed_candle(self):
        start = datetime(2026, 10, 22, 13, 30, tzinfo=timezone.utc)
        bars = [{"open": 100., "high": 100.2, "low": 99.5, "close": 100.}
                for _ in range(30)]
        for i in range(5):
            bars.append({"open": 98.8-i*.2, "high": 99.-i*.2,
                         "low": 98.4-i*.2, "close": 98.5-i*.2})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bars.csv"
            with path.open("w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["timestamp", "open", "high", "low", "close"])
                writer.writeheader()
                for i, bar in enumerate(bars):
                    writer.writerow({"timestamp": (start + timedelta(minutes=i)).isoformat(), **bar})
            loaded = load_session(path, "2026-10-22")
        result = replay_intraday([bar for _, bar in loaded], enabled=True)
        self.assertEqual(result["first_signal_index"], 32)
        first_ts = loaded[32][0]
        self.assertEqual(first_ts.isoformat(), "2026-10-22T14:02:00+00:00")
        self.assertEqual((first_ts + timedelta(minutes=1)).isoformat(),
                         "2026-10-22T14:03:00+00:00")

    def test_missing_minute_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gap.csv"
            with path.open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "open", "high", "low", "close"])
                writer.writerow(["2026-10-22T13:30:00+00:00", 100, 101, 99, 100])
                writer.writerow(["2026-10-22T13:32:00+00:00", 100, 101, 99, 100])
            with self.assertRaises(ValueError):
                load_session(path, "2026-10-22")


if __name__ == "__main__":
    unittest.main()
