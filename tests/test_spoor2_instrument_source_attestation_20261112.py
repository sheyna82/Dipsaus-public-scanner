import base64
import unittest
from research.spoor2_instrument_source_attestation_20261112 import (
    audit_instrument_source_attestation,
)


class InstrumentAttestationTests(unittest.TestCase):
    def test_missing_attestation_blocks(self):
        result = audit_instrument_source_attestation(None)
        self.assertIn("INSTRUMENT_ATTESTATION_MISSING", result["blocks"])
        self.assertFalse(result["source_attested"])

    def test_claimed_verified_does_not_approve_signer(self):
        result = audit_instrument_source_attestation({
            "verified": True,
            "signer_public_key_b64": base64.b64encode(b"a" * 32).decode(),
        })
        self.assertIn("INSTRUMENT_SIGNER_NOT_INDEPENDENTLY_APPROVED", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_invalid_signer_key_blocks(self):
        result = audit_instrument_source_attestation({"signer_public_key_b64": "bad!"})
        self.assertIn("INSTRUMENT_SIGNER_KEY_INVALID", result["blocks"])

    def test_self_signed_claim_never_attests_source(self):
        result = audit_instrument_source_attestation({
            "signer_public_key_b64": base64.b64encode(b"b" * 32).decode(),
            "signature_verified": True,
            "source_attested": True,
            "trade_ready": True,
        })
        self.assertFalse(result["source_attested"])
        self.assertFalse(result["order_placement_enabled"])


    def test_oversized_signer_key_is_rejected_before_decode(self):
        r = audit_instrument_source_attestation({"signer_public_key_b64": "A" * 100000})
        self.assertIn("INSTRUMENT_SIGNER_KEY_OVERSIZED", r["blocks"])
        self.assertFalse(r["source_attested"])


if __name__ == "__main__":
    unittest.main()
