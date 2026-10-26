import unittest
from datetime import datetime, timezone
from research_notification_forward_returns import forward_returns

class ForwardReturnTests(unittest.TestCase):
    def setUp(self):
        self.signal = datetime(2026, 10, 26, 12, 51, tzinfo=timezone.utc)
        self.bars = [{"date": f"2026-11-{i:02d}", "open": 100+i, "close": 101+i} for i in range(1, 26)]

    def test_no_same_day_entry_and_net_cost(self):
        r = forward_returns(self.signal, self.bars)
        self.assertEqual(r[3]["entry_date"], "2026-11-01")
        self.assertAlmostEqual(r[3]["net_proxy_return_pct"], r[3]["gross_return_pct"] - 0.3, places=3)
        self.assertFalse(r[3]["execution_verified"])

    def test_horizon_counts_exact_subsequent_sessions(self):
        r=forward_returns(self.signal,self.bars[:3])
        self.assertEqual(r[3]["exit_date"],"2026-11-03")
        self.assertIsNone(r[5])
        self.assertAlmostEqual(r[3]["gross_return_pct"],4.0,places=4)

    def test_missing_future_is_not_zero(self):
        self.assertIsNone(forward_returns(self.signal, self.bars[:2])[3])

    def test_no_naive_timestamp(self):
        with self.assertRaises(ValueError):
            forward_returns(datetime(2026, 10, 26), self.bars)

    def test_reject_duplicate_bars(self):
        with self.assertRaises(ValueError):
            forward_returns(self.signal, self.bars[:1] + self.bars[:1])

if __name__ == "__main__":
    unittest.main()
