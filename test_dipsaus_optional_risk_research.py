import unittest
from dipsaus_optional_risk_research import assess_risk, assess_structure_pressure


class RiskResearchTests(unittest.TestCase):
    def setUp(self):
        self.bars = [{"high": 103+i, "low": 97+i, "close": 100+i}
                     for i in range(16)]

    def test_pressure_states_do_not_sell_or_notify(self):
        context = assess_risk(self.bars, 115)
        support = context["recent_support"]
        atr = context["atr"]
        for price, expected in (
            (support + 0.01, "ABOVE_REFERENCE_SUPPORT"),
            (support - 0.25 * atr, "BELOW_SUPPORT_REVIEW"),
            (support - 0.75 * atr, "DEEPER_SUPPORT_BREACH_REVIEW"),
        ):
            outcome = assess_structure_pressure(context, price)
            self.assertEqual(outcome["state"], expected)
            self.assertFalse(outcome["sell_recommendation"])
            self.assertFalse(outcome["stop_advice_enabled"])
            self.assertFalse(outcome["notify"])
            self.assertFalse(outcome["trade_ready"])
        self.assertIsNone(assess_structure_pressure(context, float("nan")))

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
