import unittest
from dipsaus_offline_technical_risk import assess_risk

class RiskTests(unittest.TestCase):
    def setUp(self):
        self.bars = [{"high": 101+i, "low": 99+i, "close": 100+i} for i in range(20)]

    def test_risk_calculation(self):
        r = assess_risk(self.bars, 118, 130)
        self.assertEqual(r["technical_invalidation_reference"], 109)
        self.assertAlmostEqual(r["risk_reward"], 12/9, places=4)
        self.assertFalse(r["trade_ready"])
        self.assertIsNone(r["order_instruction"])

    def test_trend_break_detected(self):
        bars = list(self.bars)
        bars[-1] = {"high": 111, "low": 105, "close": 106}
        r = assess_risk(bars, 118)
        self.assertTrue(r["trend_break_below_previous_10_bar_low"])

    def test_volatility_expansion(self):
        bars = [{"high": 101, "low": 99, "close": 100} for _ in range(30)]
        for bar in bars[-14:]:
            bar.update(high=105, low=95)
        r = assess_risk(bars, 100)
        self.assertTrue(r["volatility_expansion_1_5x"])

    def test_insufficient_history_for_volatility_comparison(self):
        self.assertIsNone(assess_risk(self.bars, 118)["volatility_expansion_1_5x"])

    def test_stoploss_advice_cannot_be_enabled(self):
        self.assertIsNone(assess_risk(self.bars, 118, stoploss_advice=True))

    def test_invalid_data_rejected(self):
        self.assertIsNone(assess_risk(self.bars[:14], 118))
        self.assertIsNone(assess_risk(self.bars, float("nan")))
        self.assertIsNone(assess_risk(self.bars, 118, period=True))

    def test_no_positive_reward(self):
        self.assertIsNone(assess_risk(self.bars, 118, 0))
        self.assertIsNone(assess_risk(self.bars, 118, 110)["risk_reward"])

if __name__ == "__main__":
    unittest.main()
