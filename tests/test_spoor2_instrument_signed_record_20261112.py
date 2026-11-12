import base64
import json
import unittest
from research.spoor2_instrument_signed_record_20261112 import (
    verify_instrument_signed_record,
)

IDENTITY = {"symbol": "TEST", "market": "US",
            "venue_mic": "XNAS", "isin": "US0378331005"}


class SignedInstrumentRecordTests(unittest.TestCase):
    def test_missing_record_fails_closed(self):
        r = verify_instrument_signed_record(IDENTITY, None, "", "")
        self.assertIn("INVALID_INSTRUMENT_SIGNED_RECORD", r["blocks"])

    def test_cross_listing_mismatch_fails_before_signature(self):
        row = {**IDENTITY, "venue_mic": "XNYS"}
        r = verify_instrument_signed_record(IDENTITY, row, "", "")
        self.assertIn("INSTRUMENT_SIGNED_RECORD_BINDING_MISMATCH", r["blocks"])

    def test_invalid_signature_encoding_fails(self):
        r = verify_instrument_signed_record(IDENTITY, IDENTITY, "!", "!")
        self.assertIn("INVALID_INSTRUMENT_SIGNATURE_ENCODING", r["blocks"])

    def test_valid_signature_is_not_source_attestation(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        key = Ed25519PrivateKey.generate()
        raw = key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        payload = json.dumps(IDENTITY, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("ascii")
        r = verify_instrument_signed_record(
            IDENTITY, IDENTITY,
            base64.b64encode(key.sign(payload)).decode(),
            base64.b64encode(raw).decode())
        self.assertTrue(r["signature_verified"])
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])
        self.assertIn("INSTRUMENT_SIGNER_NOT_INDEPENDENTLY_APPROVED", r["blocks"])

    def test_tampered_signature_fails(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        key = Ed25519PrivateKey.generate()
        raw = key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        payload = json.dumps(IDENTITY, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("ascii")
        signature = bytearray(key.sign(payload))
        signature[0] ^= 1
        r = verify_instrument_signed_record(
            IDENTITY, IDENTITY, base64.b64encode(signature).decode(),
            base64.b64encode(raw).decode())
        self.assertIn("INSTRUMENT_SIGNATURE_INVALID", r["blocks"])


    def test_noncanonical_crypto_base64_blocks(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        private = Ed25519PrivateKey.generate()
        record = IDENTITY
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
                r = verify_instrument_signed_record(IDENTITY, IDENTITY, sig, pub)
                self.assertIn("INVALID_INSTRUMENT_SIGNATURE_ENCODING", r["blocks"])
                self.assertFalse(r["signature_verified"])
                self.assertFalse(r["trade_ready"])
                self.assertFalse(r["order_placement_enabled"])

    def test_isolated_unicode_surrogates_block_before_crypto(self):
        for surrogate in (chr(0xD800), chr(0xDFFF)):
            for field in ("symbol", "market", "venue_mic", "isin"):
                with self.subTest(field=field, surrogate=repr(surrogate)):
                    identity = {**IDENTITY, field: "X" + surrogate}
                    record = identity
                    r = verify_instrument_signed_record(identity, record, "", "")
                    self.assertIn("INSTRUMENT_SIGNED_RECORD_INVALID_UNICODE", r["blocks"])
                    self.assertFalse(r["signature_verified"])
                    self.assertFalse(r["trade_ready"])
                    self.assertFalse(r["order_placement_enabled"])

    def test_unicode_normalization_does_not_change_signed_identity(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        import unicodedata
        private = Ed25519PrivateKey.generate()
        nfc = "\\u00e9".encode("ascii").decode("unicode_escape")
        nfd = unicodedata.normalize("NFD", nfc)
        self.assertNotEqual(nfc, nfd)
        original = {**IDENTITY, "symbol": "T" + nfc}
        changed = {**IDENTITY, "symbol": "T" + nfd}
        record = original
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("ascii")
        sig = base64.b64encode(private.sign(payload)).decode("ascii")
        key = base64.b64encode(private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)).decode("ascii")
        verified = verify_instrument_signed_record(original, record, sig, key)
        self.assertTrue(verified["signature_verified"])
        self.assertFalse(verified["source_attested"])
        self.assertFalse(verified["trade_ready"])
        self.assertFalse(verified["order_placement_enabled"])
        mismatched = verify_instrument_signed_record(changed, record, sig, key)
        self.assertIn("INSTRUMENT_SIGNED_RECORD_BINDING_MISMATCH", mismatched["blocks"])
        self.assertFalse(mismatched["signature_verified"])
        self.assertFalse(mismatched["trade_ready"])
        self.assertFalse(mismatched["order_placement_enabled"])
        tampered = verify_instrument_signed_record(changed, changed, sig, key)
        self.assertIn("INSTRUMENT_SIGNATURE_INVALID", tampered["blocks"])
        self.assertFalse(tampered["signature_verified"])
        self.assertFalse(tampered["trade_ready"])
        self.assertFalse(tampered["order_placement_enabled"])

    def test_nonstring_identity_fields_fail_closed(self):
        for field in ("symbol", "market", "venue_mic", "isin"):
            for value in (None, 123, True, [], {}):
                with self.subTest(field=field, value=repr(value)):
                    identity = {**IDENTITY, field: value}
                    record = identity
                    r = verify_instrument_signed_record(identity, record, "", "")
                    self.assertIn("INSTRUMENT_SIGNED_RECORD_BINDING_MISMATCH", r["blocks"])
                    self.assertFalse(r["signature_verified"])
                    self.assertFalse(r["source_attested"])
                    self.assertFalse(r["trade_ready"])
                    self.assertFalse(r["order_placement_enabled"])

    def test_unverified_isin_mic_claims_never_grant_authority(self):
        identity = {**IDENTITY, "isin": "INVALID-ISIN", "venue_mic": "ZZZZ"}
        record = identity
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        private = Ed25519PrivateKey.generate()
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        sig = base64.b64encode(private.sign(payload)).decode("ascii")
        key = base64.b64encode(private.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode("ascii")
        r = verify_instrument_signed_record(identity, record, sig, key)
        self.assertTrue(r["signature_verified"])
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])
        self.assertIn("INSTRUMENT_SIGNER_NOT_INDEPENDENTLY_APPROVED", r["blocks"])

if __name__ == "__main__":
    unittest.main()
