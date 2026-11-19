"""Offline tests for instrument identity assertions; no external verification."""
import unittest
from research.spoor2_instrument_identity_20261112 import audit_instrument_identity


def fixture():
    identity = {"symbol": "AAPL", "market": "US",
                "venue_mic": "XNAS", "isin": "US0378331005"}
    return {**identity, "technical_evidence": {
        role + "_evidence": dict(identity)
        for role in ("broker", "invalidation", "resistance")
    }}


class InstrumentIdentityTests(unittest.TestCase):
    def test_consistent_identity_remains_unattested(self):
        result = audit_instrument_identity(fixture())
        self.assertEqual(result["status"], "CONSISTENT_CLAIMS_NOT_EXTERNALLY_ATTESTED")
        self.assertIn("EXTERNAL_INSTRUMENT_ATTESTATION_NOT_CONNECTED", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_wrong_listing_venue_blocks(self):
        row = fixture()
        row["technical_evidence"]["broker_evidence"]["venue_mic"] = "XNYS"
        self.assertIn("BROKER_VENUE_MIC_MISMATCH",
                      audit_instrument_identity(row)["blocks"])

    def test_wrong_isin_blocks(self):
        row = fixture()
        row["technical_evidence"]["resistance_evidence"]["isin"] = "US5949181045"
        self.assertIn("RESISTANCE_ISIN_MISMATCH",
                      audit_instrument_identity(row)["blocks"])

    def test_invalid_isin_checksum_blocks(self):
        row = fixture()
        row["isin"] = "US0378331006"
        self.assertIn("INSTRUMENT_ISIN_INVALID",
                      audit_instrument_identity(row)["blocks"])

    def test_missing_identity_blocks(self):
        row = fixture()
        del row["technical_evidence"]["invalidation_evidence"]["market"]
        self.assertIn("INVALIDATION_MARKET_NOT_DECLARED",
                      audit_instrument_identity(row)["blocks"])

    def test_claimed_verified_does_not_override_block(self):
        row = fixture()
        row["technical_evidence"]["broker_evidence"]["venue_mic"] = "XNYS"
        row["technical_evidence"]["broker_evidence"]["verified"] = True
        self.assertEqual(audit_instrument_identity(row)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
