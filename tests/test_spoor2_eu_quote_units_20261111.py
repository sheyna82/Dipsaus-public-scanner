import unittest
from decimal import Decimal
from datetime import datetime, timezone
from research.spoor2_eu_quote_units_20261111 import normalize_quote, review_fx_evidence

NOW = datetime(2026, 11, 11, 10, tzinfo=timezone.utc)

class EuropeanQuoteUnitTests(unittest.TestCase):
    def test_pence_to_pounds_exact(self):
        r = normalize_quote("125.50", "GBp")
        self.assertEqual(Decimal(r["base_price"]), Decimal("1.2550"))
        self.assertEqual(r["base_currency"], "GBP")
        self.assertFalse(r["trade_ready"])

    def test_pounds_not_scaled(self):
        self.assertEqual(Decimal(normalize_quote("125.50", "GBP")["base_price"]), Decimal("125.50"))

    def test_euro_quote_not_fx_verified(self):
        r = normalize_quote("17.25", "EUR")
        self.assertEqual(r["base_currency"], "EUR")
        self.assertFalse(r["fx_verified"])

    def test_unsupported_or_ambiguous_unit_blocks(self):
        for unit in ("gbp", "GBX", "p", "USC", None):
            self.assertEqual(normalize_quote("100", unit)["status"], "BLOCKED")

    def test_invalid_price_blocks(self):
        for value in ("NaN", "Infinity", "-1", "0", True, 1.5, None):
            self.assertEqual(normalize_quote(value, "GBp")["status"], "BLOCKED")

    def test_unverified_fx_blocks(self):
        r = review_fx_evidence({"source_currency": "GBP", "target_currency": "EUR",
              "eur_per_base_unit": "1.2", "checked_utc": NOW.isoformat()}, now_utc=NOW)
        self.assertIn("FX_NOT_INDEPENDENTLY_VERIFIED", r["blocks"])
        self.assertIn("FX_EXTERNAL_ATTESTATION_NOT_CONNECTED", r["blocks"])

    def test_claimed_verified_fx_still_blocks(self):
        r = review_fx_evidence({"source_currency": "GBP", "target_currency": "EUR",
              "eur_per_base_unit": "1.2", "checked_utc": NOW.isoformat(),
              "provider_id": "fixture", "source_record_id": "test",
              "source_url": "https://example.org/test", "verified": True}, now_utc=NOW)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("FX_EXTERNAL_ATTESTATION_NOT_CONNECTED", r["blocks"])

    def test_stale_fx_blocks(self):
        r = review_fx_evidence({"source_currency": "GBP", "target_currency": "EUR",
              "eur_per_base_unit": "1.2", "checked_utc": "2026-11-10T10:00:00Z",
              "verified": True}, now_utc=NOW)
        self.assertIn("FX_STALE_OR_FUTURE", r["blocks"])

if __name__ == "__main__":
    unittest.main()
