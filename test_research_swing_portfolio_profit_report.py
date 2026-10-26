import unittest
from research_swing_portfolio_profit_report import compare_portfolio_profit_diagnostics


def candidate(ticker, hypothesis, baseline, closes, opens):
    return {
        "ticker": ticker, "eligible": True, "entry_price": 100,
        "daily_closes": closes, "next_opens": opens,
        "hypothesis_score": hypothesis, "baseline_score": baseline,
    }


class PortfolioProfitReportTests(unittest.TestCase):
    def test_reconciles_both_arms(self):
        candidates = [
            candidate("AAA", 10, 1, [101, 102, 103], [102, 103, 104]),
            candidate("BBB", 1, 10, [99, 98, 97], [98, 97, 96]),
        ]
        result = compare_portfolio_profit_diagnostics(
            candidates, 3500, max_positions=1, tranche=3500, horizon=3,
            spread_bps=5, slippage_bps=5, commission_bps=2)
        self.assertEqual(result["comparison"]["hypothesis"]["selected"][0]["ticker"], "AAA")
        self.assertEqual(result["comparison"]["baseline"]["selected"][0]["ticker"], "BBB")
        for arm in ("hypothesis", "baseline"):
            self.assertEqual(
                result["diagnostics"][arm]["net_profit"],
                result["comparison"][arm]["portfolio_net_pnl"])
        self.assertFalse(result["independent_real_market_validation"])

    def test_legacy_execution_rejected(self):
        with self.assertRaisesRegex(ValueError, "next_open_execution_required"):
            compare_portfolio_profit_diagnostics([], 3500,
                execution_model="close_optimistic_legacy")


if __name__ == "__main__":
    unittest.main()
