import unittest

from research.spoor2_instrument_venue_fee_audit_20261113 import (
    audit_instrument_venue_fee, isin_checksum_valid,
)

C = {"symbol": "TEST", "isin": "US0378331005", "venue_mic": "XNAS",
     "market": "US", "product_type": "EQUITY", "trading_currency": "USD"}
META = {"source_url": "https://example.invalid/claim",
        "retrieved_utc": "2026-11-13T08:00:00Z",
        "source_version": "untrusted-claim",
        "independent_verification": True}


class InstrumentVenueFeeAuditTests(unittest.TestCase):
    def test_known_isin_checksum(self):
        self.assertTrue(isin_checksum_valid("US0378331005"))
        self.assertFalse(isin_checksum_valid("US0378331006"))
        self.assertFalse(isin_checksum_valid("INVALID-ISIN"))
        self.assertFalse(isin_checksum_valid(None))

    def test_missing_primary_evidence_fails_closed(self):
        r = audit_instrument_venue_fee(C)
        self.assertIn("ISIN_PRIMARY_EVIDENCE_MISSING", r["blocks"])
        self.assertIn("MIC_PRIMARY_EVIDENCE_MISSING", r["blocks"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])

    def test_bad_identity_fails_closed(self):
        for field, value in (("isin", None), ("symbol", 123),
                             ("venue_mic", []), ("market", True)):
            with self.subTest(field=field):
                r = audit_instrument_venue_fee({**C, field: value})
                self.assertIn("INVALID_INSTRUMENT_IDENTITY", r["blocks"])
                self.assertFalse(r["trade_ready"])

    def test_invalid_isin_never_becomes_registered(self):
        r = audit_instrument_venue_fee({**C, "isin": "US0378331006"})
        self.assertIn("ISIN_FORMAT_OR_CHECKSUM_INVALID", r["blocks"])
        self.assertFalse(r["isin_registered"])

    def test_untrusted_complete_claims_never_attest_authority(self):
        r = audit_instrument_venue_fee(
            C,
            isin_record={**META, "isin": C["isin"]},
            mic_record={**META, "venue_mic": C["venue_mic"]},
            listing_record={**META, **{k: C[k] for k in
                                      ("symbol", "isin", "venue_mic", "market")}},
            degiro_record={**META, **C, "broker": "DEGIRO",
                           "tariff_effective_date": "2026-11-13",
                           "tariff_rule_id": "untrusted"},
        )
        self.assertTrue(r["isin_evidence_complete"])
        self.assertTrue(r["degiro_fee_evidence_complete"])
        for key in ("isin_registered", "mic_registered", "listing_verified",
                    "degiro_fee_verified", "source_attested", "trade_ready",
                    "order_placement_enabled"):
            self.assertFalse(r[key], key)
        self.assertIn("INDEPENDENT_SOURCE_AUTHORITY_NOT_ATTESTED", r["blocks"])

    def test_wrong_venue_or_currency_cannot_match_fee(self):
        evidence = {**META, **C, "broker": "DEGIRO",
                    "tariff_effective_date": "2026-11-13",
                    "tariff_rule_id": "untrusted"}
        r = audit_instrument_venue_fee(
            C, isin_record={**META, "isin": C["isin"]},
            mic_record={**META, "venue_mic": C["venue_mic"]},
            listing_record={**META, **{k: C[k] for k in
                                      ("symbol", "isin", "venue_mic", "market")}},
            degiro_record={**evidence, "trading_currency": "EUR"},
        )
        self.assertFalse(r["degiro_fee_evidence_complete"])
        self.assertIn("DEGIRO_FEE_PRIMARY_EVIDENCE_UNVERIFIED", r["blocks"])


if __name__ == "__main__":
    unittest.main()
