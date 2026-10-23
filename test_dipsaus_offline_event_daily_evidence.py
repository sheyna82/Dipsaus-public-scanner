import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from dipsaus_offline_event_daily_evidence import derive_daily_event_evidence


class EventDailyEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "daily.csv"
        dates = []
        day = date(2026, 8, 3)
        while len(dates) < 25:
            if day.weekday() < 5:
                dates.append(day.isoformat())
            day += timedelta(days=1)
        self.last_date = dates[-1]
        with self.path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(("Date", "Open", "High", "Low", "Close", "Volume"))
            for i, d in enumerate(dates):
                close = 100 + i
                w.writerow((d, close, close + 1, close - 1, close, 1000))

    def test_real_bars_derive_trend(self):
        result = derive_daily_event_evidence(str(self.path),
                   expected_session=self.last_date, source_verified=True)
        self.assertEqual(result["status"], "OBSERVED_DAILY_ONLY")
        self.assertTrue(result["trend_confirmed"])
        self.assertFalse(result["downside_warning"])

    def test_source_unverified_blocks(self):
        self.assertEqual(derive_daily_event_evidence(str(self.path),
                         expected_session=self.last_date)["status"], "DATA_BLOCKED")

    def test_stale_session_blocks(self):
        self.assertEqual(derive_daily_event_evidence(str(self.path),
                         expected_session="2026-01-01", source_verified=True)["reason"],
                         "session_not_verified")

    def test_invalid_csv_blocks(self):
        self.assertEqual(derive_daily_event_evidence("nonexistent.csv",
                         expected_session=self.last_date, source_verified=True)["status"],
                         "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
