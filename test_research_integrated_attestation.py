import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from research_integrated_attestation import verify_historical_attestations as verify
from research_ed25519_verifier import DOMAIN

class IntegratedAttestationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        private, public = root / "private.pem", root / "public.pem"
        subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519",
                        "-out", str(private)], check=True, capture_output=True)
        subprocess.run(["openssl", "pkey", "-in", str(private),
                        "-pubout", "-out", str(public)], check=True, capture_output=True)
        cls.pem = public.read_bytes()
        cls.fp = hashlib.sha256(cls.pem).hexdigest()
        cls.key = {"key_id": "synthetic-key", "public_key_pem": cls.pem,
                   "valid_from_utc": "2026-01-01T00:00:00Z",
                   "valid_until_utc": "2026-02-01T00:00:00Z",
                   "revoked_from_utc": None}
        cls.entries = []
        for i in (1, 2):
            digest = format(i, "064x")
            message, signature = root / f"message{i}", root / f"signature{i}"
            message.write_bytes(DOMAIN + bytes.fromhex(digest))
            subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", str(private),
                            "-rawin", "-in", str(message), "-out", str(signature)],
                           check=True, capture_output=True)
            cls.entries.append({
                "sequence": i, "batch_digest": digest,
                "previous_digest": format(i - 1, "064x") if i > 1 else None,
                "closed_utc": "2026-01-10T00:00:00Z",
                "attested_utc": "2026-01-10T00:10:00Z",
                "key_id": "synthetic-key", "signature": signature.read_bytes(),
                "public_key_pem": cls.pem})

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def check(self, entries=None, keys=None, fingerprints=None):
        return verify(self.entries if entries is None else entries,
                      keys=[self.key] if keys is None else keys,
                      expected_fingerprints={"synthetic-key": self.fp}
                      if fingerprints is None else fingerprints)

    def test_integrated_synthetic_pass_still_unattested(self):
        r = self.check()
        self.assertEqual(r["status"], "INTEGRATED_ATTESTATION_RESEARCH_ONLY")
        self.assertEqual(r["verified_cryptographic_signatures"], 2)
        self.assertFalse(r["independently_attested"])
        self.assertFalse(r["trade_ready"])

    def test_tampered_signature(self):
        changed = [self.entries[0], {**self.entries[1], "signature": b"0"*64}]
        self.assertEqual(self.check(entries=changed)["reason"], "SIGNATURE_BLOCKED")

    def test_revoked_key(self):
        key = {**self.key, "revoked_from_utc": "2026-01-09T00:00:00Z"}
        self.assertEqual(self.check(keys=[key])["reason"], "KEY_POLICY_BLOCKED")

    def test_wrong_fingerprint(self):
        self.assertEqual(self.check(fingerprints={"synthetic-key": "a"*64})["reason"],
                         "KEY_POLICY_BLOCKED")

    def test_broken_chain(self):
        changed = [self.entries[0], {**self.entries[1], "previous_digest": "a"*64}]
        self.assertEqual(self.check(entries=changed)["reason"], "CHAIN_BLOCKED")

    def test_public_key_mismatch(self):
        changed = [self.entries[0], {**self.entries[1],
                                    "public_key_pem": b"-----BEGIN PUBLIC KEY-----\nother\n"}]
        self.assertEqual(self.check(entries=changed)["reason"], "KEY_MATERIAL_MISMATCH")

if __name__ == "__main__":
    unittest.main()
