"""Offline bar preflight regressions."""
import unittest
from datetime import date
from research_swing_data_preflight import validate_research_bars


class DataPreflightTests(unittest.TestCase):
    def setUp(self):
        self.days = [date(2026, 1, n) for n in (2, 5, 6)]
        self.bars = [{"date": d, "open": 100, "close": 99,
                      "volume": 1000} for d in self.days]

    def test_valid_bars_report_coverage(self):
        r = validate_research_bars({"A": self.bars}, self.days)
        self.assertEqual(r["coverage"]["A"]["sessions"], 3)
        self.assertFalse(r["source_authenticity_verified"])

    def test_duplicate_session_rejected(self):
        rows = list(self.bars)
        rows[2] = dict(rows[1])
        with self.assertRaisesRegex(ValueError, "nonchronological_or_duplicate_bars"):
            validate_research_bars({"A": rows}, self.days)

    def test_zero_price_rejected(self):
        rows = [dict(x) for x in self.bars]
        rows[1]["open"] = 0
        with self.assertRaisesRegex(ValueError, "invalid_price"):
            validate_research_bars({"A": rows}, self.days)

    def test_missing_calendar_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "bar_outside_calendar"):
            validate_research_bars({"A": self.bars}, self.days[:2])


if __name__ == "__main__":
    unittest.main()
