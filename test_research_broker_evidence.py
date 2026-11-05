import unittest
from datetime import datetime, timezone
from research_broker_evidence import assess_broker_evidence

NOW = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)

def evidence():
    return {"source": "DEGIRO_EXPORT", "account_scope": "example-account",
            "captured_at_utc": "2026-11-05T11:30:00Z",
            "positions": {"RENK": 50, "ALFEN.AS": 25},
            "open_orders": [{"symbol": "RENK", "side": "SELL", "remaining_quantity": 50}],
            "positions_complete": True, "orders_complete": True}

class BrokerEvidenceTests(unittest.TestCase):
    def test_complete_fresh_claim_is_still_not_authenticated(self):
        report = assess_broker_evidence(evidence(), now_utc=NOW)
        self.assertTrue(report["fresh"])
        self.assertTrue(report["positions_complete_claim"])
        self.assertTrue(report["orders_complete_claim"])
        self.assertEqual(report["observed_open_order_count"], 1)
        self.assertFalse(report["capacity_usable"])
        self.assertFalse(report["trade_ready"])
        self.assertFalse(report["external_authentication_verified"])

    def test_missing_open_orders_collection_fails_closed(self):
        record = evidence()
        del record["open_orders"]
        with self.assertRaisesRegex(ValueError, "MISSING_BROKER_EVIDENCE_FIELD"):
            assess_broker_evidence(record, now_utc=NOW)

    def test_partial_orders_never_imply_completeness(self):
        record = evidence()
        record["orders_complete"] = False
        report = assess_broker_evidence(record, now_utc=NOW)
        self.assertFalse(report["orders_complete_claim"])
        self.assertFalse(report["capacity_usable"])

    def test_stale_evidence(self):
        record = evidence()
        record["captured_at_utc"] = "2026-11-03T11:30:00Z"
        self.assertFalse(assess_broker_evidence(record, now_utc=NOW)["fresh"])

    def test_future_timestamp_rejected(self):
        record = evidence()
        record["captured_at_utc"] = "2026-11-06T11:30:00Z"
        with self.assertRaisesRegex(ValueError, "FUTURE_CAPTURE_TIME"):
            assess_broker_evidence(record, now_utc=NOW)

    def test_invalid_order_rejected(self):
        for order in ({"symbol": "RENK", "side": "SELL", "remaining_quantity": -1},
                      {"symbol": "RENK", "side": "BUY", "remaining_quantity": True},
                      {"symbol": "RENK", "side": "HOLD", "remaining_quantity": 5}):
            with self.subTest(order=order):
                record = evidence()
                record["open_orders"] = [order]
                with self.assertRaisesRegex(ValueError, "INVALID_OPEN_ORDER"):
                    assess_broker_evidence(record, now_utc=NOW)

    def test_invalid_position_rejected(self):
        record = evidence()
        record["positions"] = {"RENK": float("nan")}
        with self.assertRaisesRegex(ValueError, "INVALID_POSITION"):
            assess_broker_evidence(record, now_utc=NOW)

if __name__ == "__main__":
    unittest.main()
