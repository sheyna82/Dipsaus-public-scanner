import base64
import json
import unittest
from unittest.mock import patch
from research.spoor2_eu_signed_dns_observation_20261111 import verify_signed_dns_observation

class SignedDNSObservationTests(unittest.TestCase):
    def setUp(self):
        self.args=dict(url="https://data.example.org/prices",
            allowed_hosts=["data.example.org"],resolved_addresses=["8.8.8.8"],
            resolver_identity="resolver.example.org",
            observation_utc="2026-11-11T12:00:00Z",
            verification_time_utc="2026-11-11T12:01:00Z")
        self.record={"host":"data.example.org","addresses":["8.8.8.8"],
                     "resolver_identity_claim":"resolver.example.org",
                     "observation_utc_claim":"2026-11-11T12:00:00Z"}
    def _signed(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
        key=Ed25519PrivateKey.generate()
        message=json.dumps(self.record,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
        return dict(signed_record=self.record,
            signature_b64=base64.b64encode(key.sign(message)).decode(),
            trusted_public_key_b64=base64.b64encode(
                key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode())
    def test_signed_record_still_not_admitted(self):
        signed=self._signed()
        r=verify_signed_dns_observation(**self.args,**signed)
        self.assertEqual(r["status"],"SIGNED_DNS_OBSERVATION_VERIFIED_ONLY")
        self.assertTrue(r["signature_verified"])
        self.assertFalse(r["dns_admitted"])
        self.assertFalse(r["connection_authorized"])
        self.assertFalse(r["trade_ready"])
    def test_modified_address_blocks_binding(self):
        try: signed=self._signed()
        except ImportError: self.skipTest("cryptography not installed")
        signed["signed_record"]={**self.record,"addresses":["1.1.1.1"]}
        r=verify_signed_dns_observation(**self.args,**signed)
        self.assertEqual(r["blocks"],["SIGNED_RECORD_BINDING_MISMATCH"])
    def test_invalid_signature_blocks(self):
        try: signed=self._signed()
        except ImportError: self.skipTest("cryptography not installed")
        signed["signature_b64"]=base64.b64encode(b"x"*64).decode()
        r=verify_signed_dns_observation(**self.args,**signed)
        self.assertEqual(r["blocks"],["INVALID_DNS_OBSERVATION_SIGNATURE"])
    def test_expired_record_blocks(self):
        try: signed=self._signed()
        except ImportError: self.skipTest("cryptography not installed")
        r=verify_signed_dns_observation(**{**self.args,"verification_time_utc":"2026-11-11T13:00:00Z"},**signed)
        self.assertEqual(r["blocks"],["DNS_OBSERVATION_OUTSIDE_VALIDITY_WINDOW"])
    def test_invalid_time_type_blocks(self):
        try: signed=self._signed()
        except ImportError: self.skipTest("cryptography not installed")
        r=verify_signed_dns_observation(**{**self.args,"verification_time_utc":123},**signed)
        self.assertEqual(r["blocks"],["INVALID_VERIFICATION_TIME"])
    def test_unavailable_crypto_blocks(self):
        try: signed=self._signed()
        except ImportError: self.skipTest("cryptography not installed")
        with patch.dict("sys.modules",{"cryptography.hazmat.primitives.asymmetric.ed25519":None}):
            r=verify_signed_dns_observation(**self.args,**signed)
        self.assertEqual(r["blocks"],["CRYPTOGRAPHIC_VERIFIER_UNAVAILABLE"])
if __name__=="__main__": unittest.main()
