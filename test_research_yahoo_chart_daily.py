import unittest
from research_yahoo_chart_daily import parse_yahoo_chart_daily


class YahooChartDailyTests(unittest.TestCase):
    def test_daily_chart(self):
        payload = {"chart": {"error": None, "result": [{
            "meta": {"symbol": "AMD"},
            "timestamp": [1792593000, 1792679400],
            "indicators": {"quote": [{"close": [100.5, 101.25]}]}
        }]}}
        result = parse_yahoo_chart_daily(payload, expected_symbol="AMD")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["close"], "100.5")

    def test_rejects_wrong_symbol(self):
        payload = {"chart": {"error": None, "result": [{
            "meta": {"symbol": "TSLA"}, "timestamp": [1792593000],
            "indicators": {"quote": [{"close": [100]}]}
        }]}}
        with self.assertRaisesRegex(ValueError, "unexpected_symbol"):
            parse_yahoo_chart_daily(payload, expected_symbol="AMD")

    def test_rejects_bad_prices(self):
        payload = {"chart": {"error": None, "result": [{
            "meta": {"symbol": "AMD"}, "timestamp": [1792593000],
            "indicators": {"quote": [{"close": [-1]}]}
        }]}}
        with self.assertRaisesRegex(ValueError, "invalid_chart_price"):
            parse_yahoo_chart_daily(payload, expected_symbol="AMD")


if __name__ == "__main__":
    unittest.main()
