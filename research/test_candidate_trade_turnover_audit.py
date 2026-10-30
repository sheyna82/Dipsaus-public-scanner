"""Offline unit tests for descriptive accepted-trade turnover comparisons."""
import unittest
from candidate_trade_turnover_audit import audit


class TradeTurnoverAuditTests(unittest.TestCase):
    def test_shared_removed_and_added(self):
        baseline = {"accepted_signals": [
            {"symbol": "AAA", "entry_day": 1, "exit_day": 3, "net_return_pct": 4},
            {"symbol": "BBB", "entry_day": 1, "exit_day": 4, "net_return_pct": -2}],
            "realized_return_pct": 0.3}
        alternative = {"accepted_signals": [
            {"symbol": "AAA", "entry_day": 1, "exit_day": 3, "net_return_pct": 4},
            {"symbol": "CCC", "entry_day": 2, "exit_day": 5, "net_return_pct": 1}],
            "realized_return_pct": 0.5}
        report = {"portfolio_capacity_25bps": {"recovery_from_prior20_low_3to15pct":
            {"comparison": {"baseline": baseline, "filter": alternative}}}}
        result = audit(report)["comparisons"]["filter"]
        self.assertEqual((result["shared_trade_identities"], result["baseline_only"],
                          result["alternative_only"]), (1, 1, 1))
        self.assertEqual(result["baseline_only_mean_net_return_pct"], -2)
        self.assertEqual(result["alternative_only_mean_net_return_pct"], 1)
        self.assertFalse(audit(report)["trade_ready"])

    def test_shared_trade_return_mismatch_is_rejected(self):
        row = {"symbol": "AAA", "entry_day": 1, "exit_day": 3, "net_return_pct": 4}
        conflicting = {**row, "net_return_pct": 5}
        report = {"portfolio_capacity_25bps": {"recovery_from_prior20_low_3to15pct":
            {"comparison": {
                "baseline": {"accepted_signals": [row], "realized_return_pct": 1},
                "filter": {"accepted_signals": [conflicting], "realized_return_pct": 2}}}}}
        with self.assertRaisesRegex(ValueError, "SHARED_TRADE_RETURN_MISMATCH"):
            audit(report)

    def test_quarter_cohorts_use_epoch_entry_days(self):
        from datetime import date
        epoch = date(1970, 1, 1)
        q1 = (date(2026, 3, 31) - epoch).days
        q2 = (date(2026, 4, 1) - epoch).days
        rows = [
            {"symbol": "AAA", "entry_day": q1, "exit_day": q1 + 2, "net_return_pct": 2},
            {"symbol": "BBB", "entry_day": q2, "exit_day": q2 + 2, "net_return_pct": -1},
        ]
        report = {"portfolio_capacity_25bps": {"recovery_from_prior20_low_3to15pct":
            {"comparison": {"baseline": {"accepted_signals": rows,
                                           "realized_return_pct": 0.1}}}}}
        result = audit(report)["comparisons"]["baseline"]["entry_quarter_cohorts"]["baseline"]
        self.assertEqual(result["2026Q1"]["n"], 1)
        self.assertEqual(result["2026Q2"]["mean_net_trade_return_pct"], -1)
        self.assertFalse(audit(report)["comparisons"]["baseline"]["quarterly_portfolio_returns_verified"])

    def test_prior_observed_quarter_is_non_actionable(self):
        from datetime import date
        epoch = date(1970, 1, 1)
        q1 = (date(2026, 1, 5) - epoch).days
        q3 = (date(2026, 7, 6) - epoch).days
        rows = [
            {"symbol": "AAA", "entry_day": q1, "exit_day": q1 + 2, "net_return_pct": 2},
            {"symbol": "BBB", "entry_day": q3, "exit_day": q3 + 2, "net_return_pct": -1},
        ]
        report = {"portfolio_capacity_25bps": {"recovery_from_prior20_low_3to15pct":
            {"comparison": {"baseline": {"accepted_signals": rows,
                                           "realized_return_pct": 0.1}}}}}
        result = audit(report)["comparisons"]["baseline"]["prior_observed_quarter_diagnostic"]
        self.assertIsNone(result["2026Q1"]["prior_observed_quarter"])
        self.assertEqual(result["2026Q3"]["prior_observed_quarter"], "2026Q1")
        self.assertEqual(result["2026Q3"]["prior_quarter_mean_net_trade_return_pct"], 2)
        self.assertFalse(result["2026Q3"]["eligible_for_live_filter_choice"])

    def test_duplicate_accepted_trade_rejected(self):
        row = {"symbol": "AAA", "entry_day": 1, "exit_day": 3, "net_return_pct": 4}
        report = {"portfolio_capacity_25bps": {"recovery_from_prior20_low_3to15pct":
            {"comparison": {"baseline": {"accepted_signals": [row, row],
                                         "realized_return_pct": 1}}}}}
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ACCEPTED_TRADE_IDENTITY"):
            audit(report)


if __name__ == "__main__":
    unittest.main()
