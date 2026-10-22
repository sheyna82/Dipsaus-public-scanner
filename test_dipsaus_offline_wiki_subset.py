"""Offline WIKI subset importer checks; no API access."""
import csv
import tempfile
import unittest
from pathlib import Path
from dipsaus_offline_wiki_subset import convert_wiki_subset


class WikiSubsetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.src = Path(self.tmp.name) / "source.csv"
        self.dst = Path(self.tmp.name) / "out.csv"
        self.fields = ("ticker", "date", "adj_open", "adj_high",
                       "adj_low", "adj_close", "adj_volume")

    def write(self, bad=False):
        with self.src.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(self.fields)
            for i in range(35):
                w.writerow(("OTHER" if bad and i == 10 else "AAPL",
                            f"2017-02-{i+1:02d}", 10, 12, 9, 11, 100))

    def test_rejects_mixed_symbols(self):
        self.write(bad=True)
        with self.assertRaisesRegex(ValueError, "mixed_symbols"):
            convert_wiki_subset(self.src, self.dst, symbol="AAPL")
        self.assertFalse(self.dst.exists())

    def test_rejects_invalid_dates(self):
        self.write()
        with self.assertRaises(ValueError):
            convert_wiki_subset(self.src, self.dst, symbol="AAPL")
        self.assertFalse(self.dst.exists())

    def test_valid_calendar_and_adjusted_columns(self):
        import datetime
        with self.src.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(self.fields)
            for i in range(35):
                w.writerow(("AAPL", (datetime.date(2017, 1, 1) +
                            datetime.timedelta(days=i)).isoformat(),
                            10, 12, 9, 11, 100))
        result = convert_wiki_subset(self.src, self.dst, symbol="AAPL")
        self.assertEqual(result["bars"], 35)
        self.assertFalse(result["trade_ready"])
        self.assertTrue(self.dst.exists())


if __name__ == "__main__":
    unittest.main()
