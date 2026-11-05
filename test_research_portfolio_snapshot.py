import unittest
from datetime import datetime, timezone

from research_portfolio_snapshot import snapshot, reconcile_broker_positions


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

    def test_reconciliation_detects_unrecorded_and_closed_positions(self):
        report = reconcile_broker_positions(
            self.config, {"RENK": 50, "ALFEN.AS": 25, "FER": 71, "EXE": 0},
            as_of_utc="2026-11-04T18:00:00Z")
        self.assertEqual(report["broker_open_position_count"], 3)
        self.assertIsNone(report["broker_remaining_slots"])
        self.assertEqual(report["potential_slots_upper_bound"], 3)
        self.assertEqual(set(report["position_mismatches"]), {"FER"})
        self.assertFalse(report["broker_verified_claim"])
        self.assertFalse(report["trade_ready"])

    def test_reconciliation_requires_valid_timestamp_and_shares(self):
        with self.assertRaises(ValueError):
            reconcile_broker_positions(self.config, {}, as_of_utc="not-a-date")
        with self.assertRaises(ValueError):
            reconcile_broker_positions(self.config, {"EXE": True}, as_of_utc="2026-11-04T18:00:00Z")

    def test_stale_broker_evidence_never_authorizes_capacity(self):
        report = reconcile_broker_positions(
            self.config, {"RENK": 50, "ALFEN.AS": 25},
            as_of_utc="2026-11-03T12:00:00Z",
            now_utc=datetime(2026, 11, 5, 12, tzinfo=timezone.utc))
        self.assertFalse(report["broker_evidence_fresh"])
        self.assertEqual(report["broker_evidence_age_hours"], 48)
        self.assertIsNone(report["positions_agree"])
        self.assertFalse(report["portfolio_capacity_usable"])

    def test_recent_broker_evidence_still_requires_authentication(self):
        report = reconcile_broker_positions(
            self.config, {"RENK": 50, "ALFEN.AS": 25},
            as_of_utc="2026-11-05T11:30:00Z",
            now_utc=datetime(2026, 11, 5, 12, tzinfo=timezone.utc))
        self.assertTrue(report["broker_evidence_fresh"])
        self.assertFalse(report["broker_verified_claim"])
        self.assertFalse(report["portfolio_capacity_usable"])

    def test_partial_broker_list_never_claims_complete_agreement(self):
        report = reconcile_broker_positions(
            self.config, {"RENK": 50}, as_of_utc="2026-11-05T11:30:00Z",
            now_utc=datetime(2026, 11, 5, 12, tzinfo=timezone.utc))
        self.assertTrue(report["comparison_is_partial"])
        self.assertEqual(report["position_mismatches"], {})
        self.assertEqual(report["configured_positions_not_in_partial_evidence"], ["ALFEN.AS"])
        self.assertIsNone(report["broker_remaining_slots"])
        self.assertEqual(report["observed_position_count_lower_bound"], 1)
        self.assertEqual(report["potential_slots_upper_bound"], 5)
        self.assertFalse(report["actual_remaining_slots_verified"])
        self.assertIsNone(report["positions_agree"])
        self.assertFalse(report["completeness_independently_verified"])
        self.assertFalse(report["portfolio_capacity_usable"])

    def test_ticker_suffix_alias_requires_review_not_automatic_merge(self):
        report = reconcile_broker_positions(
            self.config, {"ALFEN": 25, "RENK": 50},
            as_of_utc="2026-11-05T11:30:00Z",
            now_utc=datetime(2026, 11, 5, 12, tzinfo=timezone.utc),
            complete_account_snapshot=True)
        self.assertEqual(report["possible_symbol_aliases_review_only"],
                         [{"configured_symbol": "ALFEN.AS", "broker_symbol": "ALFEN"}])
        self.assertIn("ALFEN.AS", report["position_mismatches"])
        self.assertIn("ALFEN", report["position_mismatches"])
        self.assertFalse(report["positions_agree"])

    def test_complete_broker_snapshot_treats_missing_holding_as_mismatch(self):
        report = reconcile_broker_positions(
            self.config, {"RENK": 50}, as_of_utc="2026-11-05T11:30:00Z",
            now_utc=datetime(2026, 11, 5, 12, tzinfo=timezone.utc),
            complete_account_snapshot=True)
        self.assertIn("ALFEN.AS", report["position_mismatches"])
        self.assertEqual(report["configured_positions_not_in_partial_evidence"], [])
        self.assertFalse(report["positions_agree"])

    def test_claimed_complete_snapshot_still_not_authenticated(self):
        report = reconcile_broker_positions(
            self.config, {"RENK": 50, "ALFEN.AS": 25},
            as_of_utc="2026-11-05T11:30:00Z",
            now_utc=datetime(2026, 11, 5, 12, tzinfo=timezone.utc),
            complete_account_snapshot=True)
        self.assertTrue(report["positions_agree"])
        self.assertFalse(report["completeness_independently_verified"])
        self.assertFalse(report["broker_verified_claim"])
        self.assertFalse(report["portfolio_capacity_usable"])

    def test_future_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "FUTURE_BROKER_TIMESTAMP"):
            reconcile_broker_positions(
                self.config, {}, as_of_utc="2026-11-06T12:00:00Z",
                now_utc=datetime(2026, 11, 5, 12, tzinfo=timezone.utc))

    def test_capacity_limit_is_not_a_cash_balance(self):
        report = snapshot(self.config, max_positions=2)
        self.assertEqual(report["configured_remaining_slots"], 0)
        self.assertIsNone(report["actual_cash_eur"])


if __name__ == "__main__":
    unittest.main()
