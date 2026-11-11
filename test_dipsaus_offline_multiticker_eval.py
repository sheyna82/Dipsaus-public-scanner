import unittest
from unittest.mock import patch
from dipsaus_offline_multiticker_eval import evaluate_cohort


def record(symbol, path="stock.csv"):
    return {"symbol": symbol, "csv_path": path, "source": "provider",
            "adjustment_policy": "adjusted", "asof_cutoff": "2018-03-27",
            "corporate_actions_verified": True, "benchmark_compatible_verified": True,
            "license_reviewed": True, "holdout_unseen": True}


class MultiTickerTests(unittest.TestCase):
    def test_unverified_cohort_rejected_before_loading(self):
        result = evaluate_cohort([{"symbol": "AAPL"}], "benchmark.csv")
        self.assertEqual(result["status"], "REJECTED")

    @patch("dipsaus_offline_multiticker_eval.evaluate_local_history")
    def test_any_invalid_ticker_rejects_entire_cohort(self, mock_eval):
        mock_eval.side_effect = [
            {"status": "EXPLORATORY_ONLY", "observations": 5, "selected_count": 2,
             "selected_mean_net_pct": 1.0, "always_enter_mean_net_pct": 0.5},
            {"status": "REJECTED", "reason": "unaligned_sessions"}]
        result = evaluate_cohort([record("AAPL"), record("MSFT")], "benchmark.csv")
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("MSFT:unaligned_sessions", result["reasons"])

    @patch("dipsaus_offline_multiticker_eval.evaluate_local_history")
    def test_descriptive_only_even_when_attested(self, mock_eval):
        mock_eval.return_value = {"status": "EXPLORATORY_ONLY", "observations": 5,
                                  "selected_count": 2, "selected_mean_net_pct": 1.0,
                                  "always_enter_mean_net_pct": 0.5}
        result = evaluate_cohort([record("AAPL"), record("MSFT")], "benchmark.csv")
        self.assertEqual(result["tickers"], 2)
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["independent_holdout_verified"])


if __name__ == "__main__":
    unittest.main()
