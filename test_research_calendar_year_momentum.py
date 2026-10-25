import unittest
from research_calendar_year_momentum import calendar_year_momentum


class CalendarYearMomentumTests(unittest.TestCase):
    def test_year_groups_and_disjoint_counts(self):
        from datetime import date, timedelta
        start = date(2024, 12, 1)
        dates = [(start + timedelta(days=i)).isoformat() for i in range(100)]
        stock = [{"date": day, "close": str(100 + i + (i % 5))}
                 for i, day in enumerate(dates)]
        spy = [{"date": day, "close": "100"} for day in dates]
        result = calendar_year_momentum(stock, spy)
        self.assertEqual([x["year"] for x in result["years"]], ["2024", "2025"])
        for group in result["years"]:
            self.assertEqual(group["observations"],
                             group["positive_count"] + group["negative_count"])
        self.assertFalse(result["trade_ready"])


if __name__ == "__main__":
    unittest.main()
