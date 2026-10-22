import unittest
from dipsaus_offline_return_risk_pairing import pair_return_and_downside as pair


class ReturnRiskPairingTests(unittest.TestCase):
    def inputs(self):
        return (
            {"status": "EXPLORATORY_MATCHED_DATES",
             "rows": [{"signal_date": "2025-01-01", "excess_pct_points": 2},
                      {"signal_date": "2025-02-01", "excess_pct_points": -1}]},
            {"status": "EXPLORATORY_MATCHED_DOWNSIDE",
             "rows": [{"signal_date": "2025-01-01", "extra_adverse_pct_points": -4},
                      {"signal_date": "2025-02-01", "extra_adverse_pct_points": 0}]},
        )

    def test_winning_trade_with_deeper_drawdown_is_counted(self):
        result = pair(*self.inputs())
        self.assertEqual(result["beat_market_count"], 1)
        self.assertEqual(result["beat_market_with_deeper_drawdown_count"], 1)
        self.assertFalse(result["trade_ready"])

    def test_different_dates_block(self):
        a, b = self.inputs()
        b["rows"][0]["signal_date"] = "2025-01-02"
        self.assertEqual(pair(a, b)["reason"], "event_date_mismatch")

    def test_different_counts_block(self):
        a, b = self.inputs()
        b["rows"].pop()
        self.assertEqual(pair(a, b)["reason"], "event_count_mismatch")

    def test_positive_extra_downside_blocks(self):
        a, b = self.inputs()
        b["rows"][0]["extra_adverse_pct_points"] = 1
        self.assertEqual(pair(a, b)["reason"], "invalid_metric")


if __name__ == "__main__":
    unittest.main()
