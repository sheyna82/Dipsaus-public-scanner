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


    def test_oversized_bound_identity_blocks_before_time_window(self):
        oversized = {**RECORD, "symbol": "X" * 100000}
        candidate = {**IDENTITY, "symbol": oversized["symbol"]}
        r = verify(candidate, oversized, "", "",
                   verification_utc="invalid-time")
        self.assertIn("BOUND_INSTRUMENT_RECORD_OVERSIZED", r["blocks"])
        self.assertFalse(r["signature_verified"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])

    def test_noncanonical_crypto_base64_blocks(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        private = Ed25519PrivateKey.generate()
        record = RECORD
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("ascii")
        signature = base64.b64encode(private.sign(payload)).decode("ascii")
        key = base64.b64encode(private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)).decode("ascii")
        def alternate(encoded):
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
            padding = len(encoded) - len(encoded.rstrip("="))
            self.assertIn(padding, (1, 2))
            position = len(encoded) - padding - 1
            index = alphabet.index(encoded[position])
            return encoded[:position] + alphabet[index ^ 1] + encoded[position + 1:]
        self.assertEqual(base64.b64decode(key), base64.b64decode(alternate(key)))
        self.assertEqual(base64.b64decode(signature), base64.b64decode(alternate(signature)))
        for sig, pub in ((alternate(signature), key), (signature, alternate(key))):
            with self.subTest(noncanonical_key=pub != key):
                r = verify(IDENTITY, RECORD, sig, pub, verification_utc=NOW)
                self.assertIn("INVALID_BOUND_INSTRUMENT_SIGNATURE_ENCODING", r["blocks"])
                self.assertFalse(r["signature_verified"])
                self.assertFalse(r["trade_ready"])
                self.assertFalse(r["order_placement_enabled"])

    def test_isolated_unicode_surrogates_block_before_crypto(self):
        for surrogate in (chr(0xD800), chr(0xDFFF)):
            for field in ("symbol", "market", "venue_mic", "isin"):
                with self.subTest(field=field, surrogate=repr(surrogate)):
                    identity = {**IDENTITY, field: "X" + surrogate}
                    record = {**RECORD, field: identity[field]}
                    r = verify(identity, record, "", "", verification_utc=NOW)
                    self.assertIn("BOUND_INSTRUMENT_IDENTITY_INVALID_UNICODE", r["blocks"])
                    self.assertFalse(r["signature_verified"])
                    self.assertFalse(r["trade_ready"])
                    self.assertFalse(r["order_placement_enabled"])

if __name__ == "__main__":
    unittest.main()
