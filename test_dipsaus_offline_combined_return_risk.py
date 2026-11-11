import unittest
from dipsaus_offline_combined_return_risk import evaluate_matched_return_risk as evaluate


def bars(close=105, low=95):
    return [{"date": "2025-01-%02d" % (i + 1), "open": 100,
             "close": close, "low": low} for i in range(25)]


class CombinedReturnRiskTests(unittest.TestCase):
    def test_combined_outcomes_share_same_event(self):
        result = evaluate(bars(110, 90), bars(105, 97), [0])
        self.assertEqual(result["status"], "EXPLORATORY_COMBINED_RETURN_RISK")
        self.assertEqual(result["mean_excess_pct_points"], 5)
        self.assertEqual(result["mean_extra_adverse_pct_points"], -7)
        self.assertEqual(result["beat_market_with_deeper_drawdown_count"], 1)
        self.assertFalse(result["predictive_edge_proven"])

    def test_bad_low_blocks_combined_report(self):
        stock = bars()
        stock[2]["low"] = 0
        result = evaluate(stock, bars(), [0])
        self.assertEqual(result["reason"], "downside_invalid_price")

    def test_invalid_index_blocks_combined_report(self):
        result = evaluate(bars(), bars(), [20])
        self.assertEqual(result["reason"], "return_overlap_or_invalid_index")

    def test_empty_events_do_not_imply_performance(self):
        result = evaluate(bars(), bars(), [])
        self.assertEqual(result["events"], 0)
        self.assertIsNone(result["mean_excess_pct_points"])
        self.assertFalse(result["trade_ready"])


if __name__ == "__main__":
    unittest.main()
