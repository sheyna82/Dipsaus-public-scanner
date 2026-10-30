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

    def test_duplicate_accepted_trade_rejected(self):
        row = {"symbol": "AAA", "entry_day": 1, "exit_day": 3, "net_return_pct": 4}
        report = {"portfolio_capacity_25bps": {"recovery_from_prior20_low_3to15pct":
            {"comparison": {"baseline": {"accepted_signals": [row, row],
                                         "realized_return_pct": 1}}}}}
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ACCEPTED_TRADE_IDENTITY"):
            audit(report)


if __name__ == "__main__":
    unittest.main()
