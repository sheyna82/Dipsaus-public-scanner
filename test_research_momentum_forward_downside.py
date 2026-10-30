import unittest
from decimal import Decimal
from research_momentum_forward_downside import momentum_forward_downside, chronological_forward_downside


class ForwardDownsideTests(unittest.TestCase):
    def setUp(self):
        closes = [100, 102, 104, 106, 100, 98, 110, 112, 111, 109, 115, 118, 116, 117, 120]
        self.stock = [{"date": f"2026-01-{i:02d}", "close": str(v)}
                      for i, v in enumerate(closes, 1)]
        self.spy = [{"date": r["date"], "close": "100"} for r in self.stock]

    def test_forward_downside_can_be_negative_despite_positive_momentum(self):
        report = momentum_forward_downside(self.stock, self.spy)
        first = report["observations"][0]
        self.assertTrue(first["positive_momentum"])
        self.assertLess(Decimal(first["worst_forward_stock_return_pp"]), 0)
        self.assertEqual(first["signal_session"], "2026-01-04")
        self.assertFalse(report["trade_ready"])

    def test_future_change_does_not_change_past_signal(self):
        original = momentum_forward_downside(self.stock, self.spy)
        changed = [dict(r) for r in self.stock]
        changed[6]["close"] = "250"
        revised = momentum_forward_downside(changed, self.spy)
        self.assertEqual(original["observations"][0]["positive_momentum"],
                         revised["observations"][0]["positive_momentum"])

    def test_chronological_downside_purges_boundary(self):
        result = chronological_forward_downside(self.stock, self.spy)
        self.assertEqual(result["method"], "chronological_forward_downside_diagnostic")
        self.assertGreater(result["training"]["count"], 0)
        self.assertGreater(result["holdout"]["count"], 0)
        self.assertFalse(result["predictive_skill_established"])
        for period in ("training", "holdout"):
            group = result[period]
            self.assertLessEqual(group["positive_windows_down_5pct"], group["positive_count"])
            self.assertLessEqual(group["negative_windows_down_5pct"], group["negative_count"])
            for sign in ("positive", "negative"):
                interval = group[f"{sign}_down_5pct_wilson95"]
                if interval is not None:
                    self.assertLessEqual(0, interval["lower"])
                    self.assertLessEqual(interval["lower"], interval["upper"])
                    self.assertLessEqual(interval["upper"], 1)
                    self.assertTrue(interval["assumes_independent_events"])

    def test_invalid_horizon(self):
        with self.assertRaisesRegex(ValueError, "invalid_windows"):
            momentum_forward_downside(self.stock, self.spy, horizon=0)


if __name__ == "__main__":
    unittest.main()
