"""Offline tests for research provenance metadata. No external trust asserted."""
import unittest
from datetime import datetime, timedelta, timezone
from research_net_attestation import evaluate_attested_scenario, FIELDS

NOW = datetime(2026, 11, 19, 13, 0, tzinfo=timezone.utc)


class AttestationTests(unittest.TestCase):
    def setUp(self):
        self.e = {"broker_ask": 65, "broker_bid": 64.99,
                  "invalidation": 64, "target": 70,
                  "buy_fee_eur": 4.9, "sell_fee_eur": 4.9,
                  "fx_eur_per_unit": 1, "fx_buy_fee_rate": 0,
                  "fx_sell_fee_rate": 0, "buy_slippage_per_share": 0,
                  "sell_slippage_per_share": 0,
                  "broker_quote_verified": True, "levels_verified": True,
                  "fees_verified": True, "fx_verified": True,
                  "quote_freshness_verified": True}
        self.a = {name: {"source_id": "research-evidence:" + name,
                         "observed_utc": NOW.isoformat(), "verified": True,
                         "fields": {k: self.e[k] for k in keys}}
                  for name, keys in FIELDS.items()}

    def evaluate(self):
        return evaluate_attested_scenario(self.e, self.a, market="EU", now=NOW)

    def test_complete_metadata_non_executable(self):
        result = self.evaluate()
        self.assertEqual(result["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["source_authenticity_independently_verified"])

    def test_missing_attestation_blocked(self):
        del self.a["fees"]
        self.assertEqual(self.evaluate()["reason"], "MISSING_ATTESTATION")

    def test_missing_source_blocked(self):
        self.a["fx"]["source_id"] = ""
        self.assertEqual(self.evaluate()["reason"], "INVALID_SOURCE_ID")

    def test_stale_broker_quote_blocked(self):
        self.a["broker_quote"]["observed_utc"] = (NOW-timedelta(seconds=121)).isoformat()
        self.assertEqual(self.evaluate()["reason"], "STALE_OR_FUTURE")

    def test_future_quote_blocked(self):
        self.a["broker_quote"]["observed_utc"] = (NOW+timedelta(seconds=31)).isoformat()
        self.assertEqual(self.evaluate()["reason"], "STALE_OR_FUTURE")

    def test_mismatched_broker_quote_blocked(self):
        self.a["broker_quote"]["fields"]["broker_ask"] = 66
        self.assertEqual(self.evaluate()["reason"], "VALUE_MISMATCH")

    def test_missing_field_in_attestation_blocked(self):
        del self.a["slippage"]["fields"]["sell_slippage_per_share"]
        self.assertEqual(self.evaluate()["reason"], "FIELD_SET_MISMATCH")

    def test_unverified_attestation_blocked(self):
        self.a["technical_levels"]["verified"] = False
        self.assertEqual(self.evaluate()["reason"], "NOT_VERIFIED")

    def test_naive_timestamp_blocked(self):
        self.a["fees"]["observed_utc"] = "2026-11-19T13:00:00"
        self.assertEqual(self.evaluate()["reason"], "INVALID_TIMESTAMP")

    def test_missing_evidence_blocked(self):
        del self.e["broker_ask"]
        self.assertEqual(self.evaluate()["reason"], "VALUE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
