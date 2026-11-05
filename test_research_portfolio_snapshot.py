import unittest

from research_portfolio_snapshot import snapshot


class PortfolioSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.config = {"positions": {
            "EXE": {"status": "CLOSED-SWING", "shares": 114},
            "RENK": {"status": "PROFIT-WATCH-DYNAMIC", "shares": 50},
            "ALFEN.AS": {"status": "PROFIT-WATCH-DYNAMIC", "shares": 25},
        }}

    def test_closed_historical_shares_never_use_capacity(self):
        report = snapshot(self.config)
        self.assertEqual(report["configured_active_count"], 2)
        self.assertEqual(report["configured_remaining_slots"], 4)
        self.assertEqual(report["closed_historical_symbols"], ["EXE"])
        self.assertEqual(set(report["configured_active_positions"]), {"RENK", "ALFEN.AS"})
        self.assertFalse(report["trade_ready"])
        self.assertIsNone(report["actual_available_capital_eur"])
        self.assertFalse(report["capital_adequacy_verified"])

    def test_watch_configuration_does_not_verify_broker(self):
        report = snapshot(self.config)
        self.assertEqual(report["broker_verification_required"], ["ALFEN.AS", "RENK"])
        self.assertFalse(any(x["broker_verified"] for x in report["configured_active_positions"].values()))

    def test_invalid_active_holding_fails_closed(self):
        for shares in (0, -1, True, float("inf"), None):
            with self.subTest(shares=shares):
                with self.assertRaises(ValueError):
                    snapshot({"positions": {"RENK": {"status": "PROFIT-WATCH-DYNAMIC", "shares": shares}}})

    def test_capacity_limit_is_not_a_cash_balance(self):
        report = snapshot(self.config, max_positions=2)
        self.assertEqual(report["configured_remaining_slots"], 0)
        self.assertIsNone(report["actual_cash_eur"])


if __name__ == "__main__":
    unittest.main()
