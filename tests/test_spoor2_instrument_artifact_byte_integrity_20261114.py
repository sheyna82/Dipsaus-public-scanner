"""Offline synthetic tests of declared artifact byte integrity."""
import hashlib
import unittest
from research.spoor2_instrument_artifact_byte_integrity_20261114 import verify_evidence_artifact_bytes

DATA = b"synthetic offline evidence"
SHA = hashlib.sha256(DATA).hexdigest()


class ArtifactByteIntegrityTests(unittest.TestCase):
    def test_exact_bytes_are_not_source_attestation(self):
        r = verify_evidence_artifact_bytes(DATA, SHA, len(DATA))
        self.assertTrue(r["artifact_bytes_match_declaration"])
        self.assertEqual(r["status"], "BLOCKED")
        for flag in ("source_attested", "instrument_segment_verified",
                     "broker_route_verified", "trade_ready", "order_placement_enabled"):
            self.assertFalse(r[flag])

    def test_tampered_bytes_block(self):
        r = verify_evidence_artifact_bytes(DATA + b"x", SHA, len(DATA) + 1)
        self.assertEqual(r["blocks"], ["ARTIFACT_SHA256_MISMATCH"])

    def test_wrong_length_blocks(self):
        self.assertEqual(verify_evidence_artifact_bytes(DATA, SHA, 1)["blocks"],
                         ["ARTIFACT_BYTE_COUNT_MISMATCH"])

    def test_empty_bytes_block(self):
        self.assertEqual(verify_evidence_artifact_bytes(b"", SHA, 0)["blocks"],
                         ["NONEMPTY_ARTIFACT_BYTES_REQUIRED"])

    def test_nonbytes_block(self):
        self.assertEqual(verify_evidence_artifact_bytes("text", SHA, 4)["blocks"],
                         ["NONEMPTY_ARTIFACT_BYTES_REQUIRED"])

    def test_boolean_length_blocks(self):
        self.assertEqual(verify_evidence_artifact_bytes(DATA, SHA, True)["blocks"],
                         ["VALID_DECLARED_BYTE_COUNT_REQUIRED"])

    def test_invalid_digest_blocks(self):
        self.assertEqual(verify_evidence_artifact_bytes(DATA, "x" * 64, len(DATA))["blocks"],
                         ["VALID_DECLARED_SHA256_REQUIRED"])

    def test_uppercase_hex_is_accepted_without_attestation(self):
        r = verify_evidence_artifact_bytes(DATA, SHA.upper(), len(DATA))
        self.assertTrue(r["artifact_bytes_match_declaration"])
        self.assertFalse(r["source_attested"])


if __name__ == "__main__":
    unittest.main()
