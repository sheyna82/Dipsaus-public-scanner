"""Regression tests for offline warning-risk diagnostics."""
import unittest
from unittest.mock import patch

from research.swing_lifecycle.warning_risk_diagnostics import diagnose_case, summarize


def bars(opens, lows=None, highs=None):
    from datetime import date, timedelta
    start = date(2026, 1, 1)
    lows = lows or opens
    highs = highs or opens
    return [{"date": (start + timedelta(days=i)).isoformat(),
             "open": o, "high": h, "low": l, "close": o}
            for i, (o, l, h) in enumerate(zip(opens, lows, highs))]


class RiskDiagnosticsTests(unittest.TestCase):
    @patch("research.swing_lifecycle.warning_risk_diagnostics.warning_exit_candidate")
    def test_exit_open_excludes_exit_day_intraday_extremes(self, candidate):
        candidate.return_value = {"candidate_exit_date": "2026-01-03"}
        data = bars([100, 100, 99, 96, 97],
                    lows=[100, 98, 60, 90, 95],
                    highs=[100, 101, 150, 100, 100])
        row = diagnose_case(data, ticker="TEST", entry_index=0,
                            baseline_exit_index=4)
        self.assertAlmostEqual(row["candidate_mae_pct"], -2)
        self.assertAlmostEqual(row["candidate_mfe_pct"], 1)
        self.assertTrue(row["favorable_early_exit"])
        self.assertTrue(row["avoided_decline_5pct"])

    @patch("research.swing_lifecycle.warning_risk_diagnostics.warning_exit_candidate")
    def test_post_exit_path_and_quarter(self, candidate):
        candidate.return_value = {"candidate_exit_date": "2026-01-03"}
        data = bars([100, 100, 99, 100, 98],
                    lows=[100, 100, 99, 90, 98],
                    highs=[100, 100, 99, 110, 98])
        row = diagnose_case(data, ticker="TEST", entry_index=0,
                            baseline_exit_index=4, confirmation_sessions=2)
        self.assertTrue(row["avoided_decline_5pct"])
        self.assertTrue(row["missed_rebound_5pct"])
        self.assertEqual(row["entry_quarter"], "2026-Q1")
        self.assertEqual(summarize([row])[0]["candidates"], 1)

    @patch("research.swing_lifecycle.warning_risk_diagnostics.warning_exit_candidate")
    def test_no_early_exit(self, candidate):
        candidate.return_value = {"candidate_exit_date": "2026-01-05"}
        row = diagnose_case(bars([100, 99, 98, 97, 96]),
                            ticker="TEST", entry_index=0, baseline_exit_index=4)
        self.assertFalse(row["early_exit"])
        self.assertEqual(row["return_difference_pp"], 0)
        self.assertFalse(row["missed_rebound_5pct"])


if __name__ == "__main__":
    unittest.main()
