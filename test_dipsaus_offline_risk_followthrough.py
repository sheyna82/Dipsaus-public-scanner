import unittest
from datetime import date, timedelta
from dipsaus_offline_risk_followthrough import evaluate_risk_followthrough


class FollowthroughTests(unittest.TestCase):
    def setUp(self):
        start = date(2026, 9, 1)
        self.rows = [{"date": (start + timedelta(days=i)).isoformat(),
                      "open": 100, "high": 102, "low": 98, "close": 100}
                     for i in range(6)]
        self.meta = {"split_adjusted": True, "ohlc_consistent": True,
                     "source": "synthetic-test"}

    def test_future_return_and_missing_horizon(self):
        self.rows[3].update(open=99, high=100, low=94, close=95)
        r = evaluate_risk_followthrough(self.rows, 2, (1, 3, 10), self.meta)
        self.assertEqual(r["horizons"][1]["forward_close_return_pct"], -5)
        self.assertEqual(r["horizons"][1]["worst_future_low_pct"], -6)
        self.assertIsNone(r["horizons"][10])
        self.assertIsNone(r["order_instruction"])

    def test_gap_requires_review(self):
        self.rows[3].update(open=70, high=102, low=69, close=100)
        r = evaluate_risk_followthrough(self.rows, 2, (1,), self.meta)
        self.assertTrue(r["horizons"][1]["large_gap_manual_review"])

    def test_rejects_bad_provenance_and_dates(self):
        self.assertIsNone(evaluate_risk_followthrough(self.rows, 2))
        self.rows[3]["date"] = self.rows[2]["date"]
        self.assertIsNone(evaluate_risk_followthrough(self.rows, 2, metadata=self.meta))

    def test_rejects_future_signal(self):
        self.assertIsNone(evaluate_risk_followthrough(self.rows, 6, metadata=self.meta))


if __name__ == "__main__":
    unittest.main()
