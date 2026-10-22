import unittest
from dipsaus_offline_frozen_event_market_bridge import evaluate_frozen_events_against_market


def flat_bars():
    return [{"date": "2025-01-%03d" % (i + 1), "open": 100, "high": 101,
             "low": 99, "close": 100, "volume": 1000} for i in range(50)]


class FrozenEventMarketBridgeTests(unittest.TestCase):
    def test_no_signals_does_not_invent_performance(self):
        rows = flat_bars()
        result = evaluate_frozen_events_against_market(rows, rows)
        self.assertEqual(result["status"], "EXPLORATORY_COMBINED_RETURN_RISK")
        self.assertEqual(result["events"], 0)
        self.assertIsNone(result["mean_excess_pct_points"])
        self.assertFalse(result["trade_ready"])

    def test_unaligned_market_rejected(self):
        stock, market = flat_bars(), flat_bars()
        market[1]["date"] = "2025-02-100"
        self.assertEqual(evaluate_frozen_events_against_market(stock, market)["status"], "DATA_BLOCKED")

    def test_invalid_horizon_rejected(self):
        rows = flat_bars()
        self.assertEqual(evaluate_frozen_events_against_market(rows, rows, event_horizon=1)["reason"], "invalid_horizon")


if __name__ == "__main__":
    unittest.main()
