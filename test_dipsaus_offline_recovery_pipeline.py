import unittest
from dipsaus_offline_recovery_pipeline import evaluate_recovery_research


def obs(id, published="2026-10-01T10:00:00+00:00", future_high=104):
    return {
        "id": id, "signal_time": "2026-10-01T16:00:00+00:00",
        "provenance": {"price": {"observed_at": "2026-09-30T16:00:00+00:00",
                                 "published_at": published}},
        "features": {"relative_strength_20d": 3, "return_5d": 2,
                     "volume_ratio_20d": 1.5, "atr_pct": 3,
                     "market_return_5d": 1, "days_to_earnings": 10},
        "bars": [{"date": "2026-10-01", "high": 101, "low": 99, "close": 100},
                 {"date": "2026-10-02", "high": future_high, "low": 98, "close": 102}],
    }


class RecoveryPipelineTests(unittest.TestCase):
    def test_combines_components(self):
        r = evaluate_recovery_research([obs("a")], minimum_resolved=1, horizon=1)
        self.assertEqual(r["included"], 1)
        self.assertEqual(r["evaluated"][0]["status"], "GAIN_FIRST")
        self.assertEqual(r["score_report"]["bands"]["high"]["nominated"], 1)
        self.assertFalse(r["trade_ready"])

    def test_future_feature_excluded(self):
        r = evaluate_recovery_research(
            [obs("a", published="2026-10-02T10:00:00+00:00")],
            minimum_resolved=1, horizon=1)
        self.assertEqual(r["included"], 0)
        self.assertEqual(r["excluded"][0]["reason"], "asof_unverified")

    def test_incomplete_future_data_not_hidden(self):
        r = evaluate_recovery_research([obs("a")], minimum_resolved=1, horizon=3)
        self.assertEqual(r["included"], 1)
        self.assertEqual(r["evaluated"][0]["status"], "INSUFFICIENT_FUTURE_DATA")
        self.assertEqual(r["score_report"]["bands"]["high"]["resolved"], 0)

    def test_duplicate_ids_rejected(self):
        self.assertIsNone(evaluate_recovery_research(
            [obs("a"), obs("a")], horizon=1))


if __name__ == "__main__":
    unittest.main()
