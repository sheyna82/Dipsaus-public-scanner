import unittest
from historical_portfolio_comparability import compare_historical_portfolios


class PortfolioComparabilityTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"name": "10d_50pct", "total_net_return_pct": 21.88,
                      "holdout_max_drawdown_pct": -22.56, "mean_exposure": 0.5}]

    def test_requires_explicit_comparability(self):
        result = compare_historical_portfolios(self.rows, 63.21)
        self.assertEqual(result["status"], "UNKNOWN")

    def test_descriptive_only(self):
        result = compare_historical_portfolios(self.rows, 63.21, comparable=True)
        self.assertEqual(result["status"], "DESCRIPTIVE_ONLY")
        self.assertAlmostEqual(result["rows"][0]["excess_vs_benchmark_pct_points"], -41.33)
        self.assertIs(result["trade_ready"], False)
        self.assertIs(result["rows"][0]["risk_adjusted_edge_proven"], False)

    def test_invalid_exposure_fails_closed(self):
        self.rows[0]["mean_exposure"] = 0
        self.assertEqual(compare_historical_portfolios(self.rows, 63.21, True)["status"],
                         "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
