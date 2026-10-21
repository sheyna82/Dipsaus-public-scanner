import unittest
from datetime import date, timedelta
from dipsaus_offline_recovery_holdout_report import evaluate_holdout_recovery


def observation(i, start):
    d = start + timedelta(days=i)
    following = d + timedelta(days=1)
    features = {"relative_strength_20d": 3, "return_5d": 2,
                "volume_ratio_20d": 1.5, "atr_pct": 3,
                "market_return_5d": 1, "days_to_earnings": 10}
    signal = d.isoformat()
    prior = (d - timedelta(days=1)).isoformat()
    return {"id": f"synthetic-{i}", "signal_time": signal + "T16:00:00+00:00",
            "features": features,
            "provenance": {k: {"observed_at": prior + "T10:00:00+00:00",
                               "published_at": prior + "T11:00:00+00:00"}
                           for k in features},
            "bars": [{"date": signal, "high": 101, "low": 99, "close": 100},
                     {"date": following.isoformat(), "high": 104, "low": 99, "close": 103}]}


class HoldoutReportTests(unittest.TestCase):
    def test_development_and_holdout_separate(self):
        rows = [observation(i, date(2026, 9, 1)) for i in range(12)]
        r = evaluate_holdout_recovery(rows, embargo_sessions=1,
                                      horizon=1, minimum_resolved=1)
        self.assertEqual(r["holdout_nominated"], 3)
        self.assertEqual(r["holdout_included"], 3)
        self.assertEqual(r["holdout"]["bands"]["high"]["nominated"], 3)
        self.assertGreater(r["purged_count"], 0)
        self.assertFalse(r["historical_performance_validated"])
        self.assertFalse(r["trade_ready"])

    def test_invalid_data_rejected(self):
        self.assertIsNone(evaluate_holdout_recovery([], horizon=1))


if __name__ == "__main__":
    unittest.main()
