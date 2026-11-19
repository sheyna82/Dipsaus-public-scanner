"""Offline metadata-only manifest privacy and integrity tests."""
import unittest
from datetime import datetime, timezone
from research_evidence_manifest import build_manifest, GROUPS

NOW = datetime(2026, 11, 19, 13, 0, tzinfo=timezone.utc)
DIGEST = "a" * 64


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.groups = {name: {"source_class": "BROKER" if name in ("broker_quote", "fees") else "MANUAL_RESEARCH",
                              "observed_utc": NOW.isoformat(), "verified": True,
                              "digest_sha256": DIGEST} for name in GROUPS}

    def build(self, **kwargs):
        return build_manifest(self.groups, instrument_id=kwargs.get("instrument_id", "NL0010273215"),
                              market=kwargs.get("market", "EU"), now=NOW)

    def test_manifest_never_trade_ready(self):
        r = self.build()
        self.assertEqual(r["status"], "METADATA_ONLY_UNAUTHENTICATED")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["source_authenticity_independently_verified"])

    def test_no_raw_values_in_manifest(self):
        r = self.build()
        self.assertNotIn("broker_ask", str(r))
        self.assertNotIn("account", str(r))
        self.assertNotIn("source_id", str(r))

    def test_deterministic_digest(self):
        self.assertEqual(self.build()["manifest_sha256"], self.build()["manifest_sha256"])

    def test_reject_raw_quote_field(self):
        self.groups["broker_quote"]["broker_ask"] = 123
        self.assertEqual(self.build()["reason"], "UNSAFE_FIELDS")

    def test_reject_account_identifier(self):
        self.assertEqual(self.build(instrument_id="ACCOUNT1234")["reason"], "INVALID_INSTRUMENT")

    def test_reject_extra_group(self):
        self.groups["personal"] = {}
        self.assertEqual(self.build()["reason"], "INVALID_GROUPS")

    def test_reject_unverified_string(self):
        self.groups["fees"]["verified"] = "true"
        self.assertEqual(self.build()["reason"], "INVALID_VERIFICATION")

    def test_reject_invalid_digest(self):
        self.groups["fx"]["digest_sha256"] = "not-a-digest"
        self.assertEqual(self.build()["reason"], "INVALID_DIGEST")

    def test_reject_naive_timestamp(self):
        self.groups["slippage"]["observed_utc"] = "2026-11-19T13:00:00"
        self.assertEqual(self.build()["reason"], "INVALID_TIMESTAMP")

    def test_reject_untrusted_source_class(self):
        self.groups["fees"]["source_class"] = "UNKNOWN"
        self.assertEqual(self.build()["reason"], "INVALID_SOURCE_CLASS")


if __name__ == "__main__":
    unittest.main()
