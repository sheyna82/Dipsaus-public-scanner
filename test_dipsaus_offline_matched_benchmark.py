import unittest
from dipsaus_offline_matched_benchmark import matched_event_comparison as compare


def bars(open_price=100, close_price=101):
    return [{"date": "2025-01-%02d" % (i + 1), "open": open_price,
             "close": close_price} for i in range(20)]


class MatchedBenchmarkTests(unittest.TestCase):
    def test_same_dates_and_fees(self):
        stock, market = bars(100, 110), bars(100, 105)
        result = compare(stock, market, [0], horizon=10)
        self.assertEqual(result["status"], "EXPLORATORY_MATCHED_DATES")
        self.assertAlmostEqual(result["mean_excess_pct_points"], 5.0)
        self.assertAlmostEqual(result["rows"][0]["stock_net_pct"], 9.8)
        self.assertFalse(result["trade_ready"])

    def test_overlap_blocks(self):
        self.assertEqual(compare(bars(), bars(), [0, 5], horizon=10)["reason"],
                         "overlap_or_invalid_index")

    def test_unaligned_sessions_block(self):
        stock, market = bars(), bars()
        market[0]["date"] = "2024-12-31"
        self.assertEqual(compare(stock, market, [0])["reason"], "unaligned_dates")

    def test_bad_price_blocks(self):
        stock, market = bars(), bars()
        stock[1]["open"] = 0
        self.assertEqual(compare(stock, market, [0])["reason"], "invalid_price")

    def test_no_events_not_evidence(self):
        result = compare(bars(), bars(), [])
        self.assertIsNone(result["mean_excess_pct_points"])
        self.assertFalse(result["independent_holdout"])


if __name__ == "__main__":
    unittest.main()
