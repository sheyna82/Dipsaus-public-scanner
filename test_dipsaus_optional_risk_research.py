import unittest
from dipsaus_optional_risk_research import assess_risk


class RiskResearchTests(unittest.TestCase):
    def setUp(self):
        self.bars = [{"high": 103+i, "low": 97+i, "close": 100+i}
                     for i in range(16)]

    def test_offline_advisory_only(self):
        result = assess_risk(self.bars, 115)
        self.assertIsNotNone(result)
        self.assertGreater(result["atr"], 0)
        self.assertFalse(result["stop_advice_enabled"])
        self.assertFalse(result["stop_order_created"])
        self.assertFalse(result["notify"])
        self.assertFalse(result["trade_ready"])

    def test_optional_stop_never_silently_enabled(self):
        self.assertIsNone(assess_risk(self.bars, 115, optional_stop_advice=True))

    def test_invalid_data_fails_closed(self):
        self.assertIsNone(assess_risk(self.bars[:4], 115))
        self.assertIsNone(assess_risk(self.bars, 0))
        self.assertIsNone(assess_risk(self.bars, 115, lookback=True))
        invalid = [dict(x) for x in self.bars]
        invalid[-1]["high"] = float("nan")
        self.assertIsNone(assess_risk(invalid, 115))


if __name__ == "__main__":
    unittest.main()
