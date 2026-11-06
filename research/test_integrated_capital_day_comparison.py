"""Capital-day comparison regression tests; no trading functions."""
import unittest
from integrated_capital_day_comparison import compare

def trade(id="A", allocation=3500, days=10, gross=140, costs=17.5):
    return {"id": id, "allocation_eur": allocation, "holding_sessions": days,
            "gross_pnl_eur": gross, "total_costs_eur": costs,
            "research_only": True, "trade_ready": False}

class CapitalDayTests(unittest.TestCase):
    def test_net_pnl_and_efficiency(self):
        result = compare([trade()])
        self.assertEqual(result["rows"][0]["net_pnl_eur"], "122.5")
        self.assertEqual(result["rows"][0]["net_pnl_per_1000_eur_session"], "3.5")
        self.assertFalse(result["portfolio_validated"])
        self.assertFalse(result["trade_ready"])

    def test_higher_return_same_capital_days(self):
        result = compare([trade("A"), trade("B", gross=210)])
        self.assertGreater(float(result["rows"][1]["net_pnl_per_1000_eur_session"]),
                           float(result["rows"][0]["net_pnl_per_1000_eur_session"]))

    def test_longer_hold_reduces_efficiency(self):
        result = compare([trade("A"), trade("B", days=20)])
        self.assertLess(float(result["rows"][1]["net_pnl_per_1000_eur_session"]),
                        float(result["rows"][0]["net_pnl_per_1000_eur_session"]))

    def test_zero_holding_days_blocks(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TRADE_INPUT"):
            compare([trade(days=0)])

    def test_negative_costs_blocks(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TRADE_INPUT"):
            compare([trade(costs=-1)])

    def test_allocation_above_capital_blocks(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TRADE_INPUT"):
            compare([trade(allocation=50001)])

    def test_duplicate_id_blocks(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_TRADE_ID"):
            compare([trade(), trade()])

    def test_unverified_trade_blocks(self):
        t = trade()
        t["research_only"] = False
        with self.assertRaisesRegex(ValueError, "TRADE_NOT_RESEARCH_ONLY"):
            compare([t])

    def test_nan_blocks(self):
        with self.assertRaisesRegex(ValueError, "NONFINITE_NUMBER"):
            compare([trade(gross="NaN")])

    def test_invalid_portfolio_limit_blocks(self):
        with self.assertRaisesRegex(ValueError, "INVALID_PORTFOLIO_LIMITS"):
            compare([trade()], max_positions=0)

if __name__ == "__main__":
    unittest.main()
