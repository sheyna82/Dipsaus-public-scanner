"""Offline cross-source identity conflict tests."""
import unittest
from datetime import datetime, timedelta, timezone
from research_instrument_corroboration import compare_instrument_records

NOW = datetime(2026, 11, 19, 13, tzinfo=timezone.utc)


class CrossSourceTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"source_class": "EXCHANGE", "source_id": "exchange-registry",
             "isin": "NL0010273215", "operating_mic": "XAMS",
             "segment": "official-segment-claim", "active": True,
             "observed_utc": NOW.isoformat(), "verified": True},
            {"source_class": "OFFICIAL_MIC_REGISTER", "source_id": "iso-mic",
             "isin": "NL0010273215", "operating_mic": "XAMS",
             "active": True, "observed_utc": NOW.isoformat(), "verified": True},
            {"source_class": "BROKER", "source_id": "broker-route",
             "isin": "NL0010273215", "operating_mic": "XAMS",
             "route_verified": True, "active": True,
             "observed_utc": NOW.isoformat(), "verified": True}]

    def check(self):
        return compare_instrument_records(self.rows, now=NOW)

    def test_consistent_still_not_trade_ready(self):
        r = self.check()
        self.assertEqual(r["status"], "CROSS_SOURCE_CLAIMS_CONSISTENT")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["source_authenticity_independently_verified"])

    def test_conflicting_mic(self):
        self.rows[1]["operating_mic"] = "XETR"
        self.assertEqual(self.check()["reason"], "IDENTITY_CONFLICT")

    def test_conflicting_isin(self):
        self.rows[2]["isin"] = "DE0006231004"
        self.assertEqual(self.check()["reason"], "IDENTITY_CONFLICT")

    def test_missing_broker(self):
        self.rows.pop()
        self.assertEqual(self.check()["reason"], "RECORD_COUNT")

    def test_public_provider_not_official_registry(self):
        self.rows[1]["source_class"] = "PUBLIC_PROVIDER"
        self.assertEqual(self.check()["reason"], "SOURCE_CLASS")

    def test_same_source_id_not_independent(self):
        self.rows[1]["source_id"] = "exchange-registry"
        self.assertEqual(self.check()["reason"], "SOURCE_ID")

    def test_unverified_record(self):
        self.rows[0]["verified"] = False
        self.assertEqual(self.check()["reason"], "UNVERIFIED_RECORD")

    def test_stale_registry_claim(self):
        self.rows[1]["observed_utc"] = (NOW-timedelta(days=2)).isoformat()
        self.assertEqual(self.check()["reason"], "STALE_RECORD")

    def test_inactive_listing(self):
        self.rows[0]["active"] = False
        self.assertEqual(self.check()["reason"], "INACTIVE_OR_UNVERIFIED")

    def test_missing_segment(self):
        del self.rows[0]["segment"]
        self.assertEqual(self.check()["reason"], "MISSING_SEGMENT")

    def test_unverified_broker_route(self):
        self.rows[2]["route_verified"] = False
        self.assertEqual(self.check()["reason"], "BROKER_ROUTE_BLOCKED")

    def test_duplicate_class(self):
        self.rows[1]["source_class"] = "EXCHANGE"
        self.assertEqual(self.check()["reason"], "DUPLICATE_SOURCE_CLASS")


if __name__ == "__main__":
    unittest.main()
