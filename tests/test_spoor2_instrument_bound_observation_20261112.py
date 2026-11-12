import base64
import json
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from research.spoor2_instrument_bound_observation_20261112 import (
    verify_bound_instrument_observation as verify,
)

IDENTITY = {"symbol": "TEST", "market": "US", "venue_mic": "XNAS",
            "isin": "US0378331005"}
RECORD = {**IDENTITY, "observed_utc": "2026-11-12T10:00:00Z",
          "challenge_nonce": "a" * 32}
NOW = "2026-11-12T10:02:00Z"


def signed(record):
    private = Ed25519PrivateKey.generate()
    key = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw)
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode("ascii")
    return base64.b64encode(private.sign(payload)).decode(), base64.b64encode(key).decode()


class BoundInstrumentObservationTests(unittest.TestCase):
    def test_valid_bound_signature_still_unattested(self):
        sig, key = signed(RECORD)
        r = verify(IDENTITY, RECORD, sig, key, verification_utc=NOW)
        self.assertTrue(r["signature_verified"])
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["replay_prevented"])
        self.assertIn("INSTRUMENT_NONCE_SINGLE_USE_NOT_ENFORCED", r["blocks"])

    def test_timestamp_tampering_breaks_signature(self):
        sig, key = signed(RECORD)
        changed = {**RECORD, "observed_utc": "2026-11-12T10:01:00Z"}
        r = verify(IDENTITY, changed, sig, key, verification_utc=NOW)
        self.assertIn("BOUND_INSTRUMENT_SIGNATURE_INVALID", r["blocks"])

    def test_nonce_tampering_breaks_signature(self):
        sig, key = signed(RECORD)
        changed = {**RECORD, "challenge_nonce": "b" * 32}
        r = verify(IDENTITY, changed, sig, key, verification_utc=NOW)
        self.assertIn("BOUND_INSTRUMENT_SIGNATURE_INVALID", r["blocks"])

    def test_identity_tampering_blocks(self):
        sig, key = signed(RECORD)
        changed = {**RECORD, "venue_mic": "XNYS"}
        r = verify(IDENTITY, changed, sig, key, verification_utc=NOW)
        self.assertIn("BOUND_INSTRUMENT_IDENTITY_MISMATCH", r["blocks"])

    def test_stale_signed_record_blocks(self):
        sig, key = signed(RECORD)
        r = verify(IDENTITY, RECORD, sig, key,
                   verification_utc="2026-11-12T10:06:00Z")
        self.assertIn("INSTRUMENT_OBSERVATION_OUTSIDE_WINDOW", r["blocks"])

    def test_missing_record_blocks(self):
        r = verify(IDENTITY, None, "", "", verification_utc=NOW)
        self.assertIn("INVALID_BOUND_INSTRUMENT_RECORD", r["blocks"])


if __name__ == "__main__":
    unittest.main()
