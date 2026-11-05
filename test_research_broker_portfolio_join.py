import unittest
from datetime import datetime, timezone
from research_broker_portfolio_join import reconcile_with_broker_evidence

NOW = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)
CONFIG = {"positions": {"RENK": {"status": "PROFIT-WATCH-DYNAMIC", "shares": 50},
                        "ALFEN.AS": {"status": "PROFIT-WATCH-DYNAMIC", "shares": 25},
                        "EXE": {"status": "CLOSED-SWING", "shares": 114}}}

def evidence():
    return {"source": "DEGIRO_EXPORT", "account_scope": "example",
            "captured_at_utc": "2026-11-05T11:30:00Z",
            "positions": {"RENK": 50, "ALFEN": 25, "FER": 71},
            "open_orders": [{"symbol": "RENK", "side": "SELL", "remaining_quantity": 50}],
            "positions_complete": True, "orders_complete": True}

class BrokerPortfolioJoinTests(unittest.TestCase):
    def test_complete_claim_still_never_authorizes_capacity(self):
        report = reconcile_with_broker_evidence(CONFIG, evidence(), now_utc=NOW)
        self.assertFalse(report["portfolio_capacity_usable"])
        self.assertFalse(report["trade_ready"])
        self.assertIsNone(report["actual_remaining_slots"])
        self.assertEqual(report["open_orders_observed_count"], 1)
        self.assertIn("FER", report["portfolio_comparison"]["position_mismatches"])
        self.assertFalse(report["portfolio_comparison"]["positions_agree"])

    def test_partial_snapshot_remains_partial(self):
        record = evidence()
        record["positions_complete"] = False
        record["orders_complete"] = False
        report = reconcile_with_broker_evidence(CONFIG, record, now_utc=NOW)
        self.assertTrue(report["portfolio_comparison"]["comparison_is_partial"])
        self.assertIsNone(report["portfolio_comparison"]["positions_agree"])
        self.assertFalse(report["open_orders_completeness_claim"])
        self.assertFalse(report["portfolio_capacity_usable"])

    def test_alias_with_metadata_still_requires_review(self):
        identity = {"isin": "NL0012817175", "mic": "XAMS",
                    "currency": "EUR", "instrument_type": "EQUITY"}
        report = reconcile_with_broker_evidence(
            CONFIG, evidence(), now_utc=NOW,
            configured_instruments={"ALFEN.AS": identity},
            broker_instruments={"ALFEN": identity})
        reviews = report["portfolio_comparison"]["instrument_identity_reviews"]
        match = next(x for x in reviews if x["configured_symbol"] == "ALFEN.AS")
        self.assertEqual(match["status"], "METADATA_MATCH_UNAUTHENTICATED")
        self.assertFalse(match["automatic_merge_allowed"])
        self.assertFalse(report["trade_ready"])

    def test_invalid_order_blocks_join(self):
        record = evidence()
        record["open_orders"][0]["remaining_quantity"] = -1
        with self.assertRaisesRegex(ValueError, "INVALID_OPEN_ORDER"):
            reconcile_with_broker_evidence(CONFIG, record, now_utc=NOW)

    def test_stale_broker_data_never_verifies_capacity(self):
        record = evidence()
        record["captured_at_utc"] = "2026-11-03T11:30:00Z"
        report = reconcile_with_broker_evidence(CONFIG, record, now_utc=NOW)
        self.assertFalse(report["evidence"]["fresh"])
        self.assertFalse(report["portfolio_capacity_usable"])

if __name__ == "__main__":
    unittest.main()
