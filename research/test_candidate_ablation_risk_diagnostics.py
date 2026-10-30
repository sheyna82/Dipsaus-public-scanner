"""Offline deterministic tests for research-only risk diagnostics."""
import unittest
from candidate_ablation_risk_diagnostics import FILTERS, summarize, compare


class RiskDiagnosticsTests(unittest.TestCase):
    def test_empty_is_blocked(self):
        self.assertFalse(summarize([])["trade_ready"])
        self.assertEqual(summarize([])["status"], "INSUFFICIENT_OBSERVATIONS")

    def test_mae_and_returns(self):
        rows = [
            {"net_return_pct": 2, "excess_pct": 1, "mae_pct": -4, "session_day": 1},
            {"net_return_pct": -1, "excess_pct": -2, "mae_pct": -11, "session_day": 1},
        ]
        s = summarize(rows)
        self.assertEqual(s["n"], 2)
        self.assertEqual(s["distinct_entry_days"], 1)
        self.assertEqual(s["mean_mae_pct"], -7.5)
        self.assertEqual(s["mae_breach_fraction"], {"3": 1.0, "5": 0.5, "10": 0.5})
        self.assertFalse(s["trade_ready"])

    def test_invalid_record_is_rejected(self):
        with self.assertRaises(ValueError):
            summarize([{"net_return_pct": float("nan"), "excess_pct": 1,
                        "mae_pct": -1, "session_day": 1}])

    def test_comparison_is_not_trade_ready(self):
        row = {"net_return_pct": 1, "excess_pct": 0.5,
               "mae_pct": -2, "session_day": 1}
        result = compare({key: [row] for key in FILTERS})
        self.assertFalse(result["trade_ready"])
        self.assertEqual(result["filters"]["volume_ratio_20d"]["delta_mean_mae_vs_baseline_pp"], 0)

    def test_missing_cohort_rejected(self):
        with self.assertRaises(ValueError):
            compare({"baseline": []})


if __name__ == "__main__":
    unittest.main()
