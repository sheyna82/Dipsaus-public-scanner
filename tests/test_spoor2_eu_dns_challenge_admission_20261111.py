import base64
import json
import os
import tempfile
import hashlib
import sqlite3
from unittest.mock import patch
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from research.spoor2_eu_dns_challenge_admission_20261111 import review_dns_challenge_admission

class DNSChallengeAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db=os.path.join(self.temp.name,"challenge.sqlite3")
        self.key=Ed25519PrivateKey.generate()
        self.record=dict(host="data.example.org",addresses=["8.8.8.8"],
            resolver_identity_claim="resolver.example.org",
            observation_utc_claim="2026-11-11T12:00:00Z",
            challenge_nonce="a"*64)
        payload=json.dumps(self.record,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
        self.args=dict(url="https://data.example.org/prices",
            allowed_hosts=["data.example.org"],resolved_addresses=["8.8.8.8"],
            resolver_identity="resolver.example.org",
            observation_utc="2026-11-11T12:00:00Z",
            verification_time_utc="2026-11-11T12:01:00Z",
            challenge_nonce="a"*64,signed_record=self.record,
            signature_b64=base64.b64encode(self.key.sign(payload)).decode(),
            trusted_public_key_b64=base64.b64encode(
                self.key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode())
    def test_valid_signature_untrusted_signer_does_not_consume(self):
        r=review_dns_challenge_admission(self.db,**self.args)
        self.assertEqual(r["blocks"],["SIGNER_NOT_INDEPENDENTLY_TRUSTED"])
        self.assertFalse(r["consumed"])
        self.assertFalse(os.path.exists(self.db))
    def test_invalid_signature_does_not_consume(self):
        r=review_dns_challenge_admission(self.db,**{**self.args,"signature_b64":"bad"})
        self.assertEqual(r["blocks"],["SIGNATURE_NOT_VERIFIED"])
        self.assertFalse(os.path.exists(self.db))
    def test_trusted_fixture_consumes_exact_signed_record_digest(self):
        payload=json.dumps(self.record,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
        with patch("research.spoor2_eu_signed_dns_observation_20261111.review_dns_signer_trust_anchor",return_value={"key_trusted":True,"blocks":[]}), patch("research.spoor2_eu_dns_challenge_admission_20261111.review_dns_challenge_issuance",return_value={"issued":True,"issuer_attested":True,"blocks":[]}):
            r=review_dns_challenge_admission(self.db,**self.args)
            self.assertTrue(r["consumed"])
            self.assertFalse(r["dns_admitted"])
            with sqlite3.connect(self.db) as conn:
                row=conn.execute("SELECT nonce,observation_sha256 FROM consumed_challenges").fetchone()
            self.assertEqual(row,("a"*64,hashlib.sha256(payload).hexdigest()))
            replay=review_dns_challenge_admission(self.db,**self.args)
            self.assertEqual(replay["blocks"],["CHALLENGE_CONSUMPTION_FAILED"])
            self.assertEqual(replay["ledger_blocks"],["DNS_CHALLENGE_ALREADY_CONSUMED"])
    def test_unissued_nonce_blocks_even_with_trusted_test_key(self):
        with patch("research.spoor2_eu_signed_dns_observation_20261111.review_dns_signer_trust_anchor",return_value={"key_trusted":True,"blocks":[]}):
            r=review_dns_challenge_admission(self.db,**self.args)
        self.assertEqual(r["blocks"],["CHALLENGE_ISSUANCE_NOT_VERIFIED"])
        self.assertFalse(os.path.exists(self.db))
    def test_claimed_issuer_does_not_authorize_consumption(self):
        from research.spoor2_eu_dns_challenge_issuance_20261111 import issue_dns_challenge
        issuance_db=os.path.join(self.temp.name,"issued.sqlite3")
        issue_dns_challenge(issuance_db,nonce="a"*64,issuer_id="self-declared")
        with patch("research.spoor2_eu_signed_dns_observation_20261111.review_dns_signer_trust_anchor",return_value={"key_trusted":True,"blocks":[]}):
            r=review_dns_challenge_admission(self.db,issuance_database_path=issuance_db,**self.args)
        self.assertEqual(r["blocks"],["CHALLENGE_ISSUER_NOT_ATTESTED"])
        self.assertFalse(os.path.exists(self.db))
    def test_missing_nonce_does_not_consume(self):
        r=review_dns_challenge_admission(self.db,**{**self.args,"challenge_nonce":None})
        self.assertEqual(r["blocks"],["SIGNATURE_NOT_VERIFIED"])
        self.assertFalse(os.path.exists(self.db))
if __name__=="__main__": unittest.main()
