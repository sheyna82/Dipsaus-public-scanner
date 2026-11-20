import subprocess
import tempfile
import unittest
from pathlib import Path
from research_ed25519_verifier import verify_ed25519_batch, DOMAIN

DIGEST = "a" * 64

class Ed25519VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.private = root / "private.pem"
        cls.public = root / "public.pem"
        cls.message = root / "message.bin"
        cls.signature = root / "signature.bin"
        subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519",
                        "-out", str(cls.private)], check=True, capture_output=True)
        subprocess.run(["openssl", "pkey", "-in", str(cls.private),
                        "-pubout", "-out", str(cls.public)],
                       check=True, capture_output=True)
        cls.message.write_bytes(DOMAIN + bytes.fromhex(DIGEST))
        subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", str(cls.private),
                        "-rawin", "-in", str(cls.message), "-out", str(cls.signature)],
                       check=True, capture_output=True)
        cls.pub = cls.public.read_bytes()
        cls.sig = cls.signature.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_valid_signature(self):
        result = verify_ed25519_batch(DIGEST, self.sig, self.pub)
        self.assertEqual(result["status"], "ED25519_SIGNATURE_VALID")
        self.assertTrue(result["cryptographic_signature_valid"])
        self.assertFalse(result["independently_attested"])
        self.assertFalse(result["trade_ready"])

    def test_tampered_batch(self):
        self.assertEqual(verify_ed25519_batch("b"*64, self.sig, self.pub)["status"],
                         "ED25519_SIGNATURE_INVALID")

    def test_tampered_signature(self):
        bad = bytes([self.sig[0] ^ 1]) + self.sig[1:]
        self.assertEqual(verify_ed25519_batch(DIGEST, bad, self.pub)["status"],
                         "ED25519_SIGNATURE_INVALID")

    def test_invalid_digest(self):
        self.assertEqual(verify_ed25519_batch("bad", self.sig, self.pub)["reason"],
                         "INVALID_CRYPTO_INPUT")

    def test_private_key_rejected(self):
        self.assertEqual(verify_ed25519_batch(
            DIGEST, self.sig, self.private.read_bytes())["reason"],
            "INVALID_CRYPTO_INPUT")

if __name__ == "__main__":
    unittest.main()
