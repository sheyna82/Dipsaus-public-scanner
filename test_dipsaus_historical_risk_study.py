import unittest
from datetime import date, timedelta
from dipsaus_historical_risk_study import study_historical_bars


class HistoricalRiskTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"date": (date(2026, 1, 1) + timedelta(days=i)).isoformat(),
             "high": 102, "low": 98, "close": 100}
            for i in range(22)
        ]

    def test_future_only_after_signal(self):
        self.rows[16]["close"] = 97.5
        self.rows[17]["close"] = 95
        self.rows[18]["close"] = 99
        result = study_historical_bars(self.rows, 15, 3)
        self.assertEqual(result["observation_dates"], [r["date"] for r in self.rows[16:19]])
        self.assertEqual(result["risk_states"],
                         ["BELOW_SUPPORT_REVIEW", "DEEPER_SUPPORT_BREACH_REVIEW",
                          "ABOVE_REFERENCE_SUPPORT"])
        self.assertFalse(result["source_verified"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["automatic_sell"])

    def test_invalid_dates_and_short_history_fail_closed(self):
        self.assertIsNone(study_historical_bars(self.rows, 2))
        self.assertIsNone(study_historical_bars(self.rows, 15, 9))
        bad = [dict(row) for row in self.rows]
        bad[4]["date"] = bad[3]["date"]
        self.assertIsNone(study_historical_bars(bad, 15, 3))


if __name__ == "__main__":
    unittest.main()
