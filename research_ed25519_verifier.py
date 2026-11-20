"""Offline Ed25519 signature verification using OpenSSL CLI.

Research-only. The verifier receives a public key and signature; private keys
are never accepted. Cryptographic validity is not independent source trust.
"""
import re
import subprocess
import tempfile
from pathlib import Path

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False,
           "archive_integrity_independently_verified": False}
HEX = re.compile(r"[0-9a-f]{64}\Z")
DOMAIN = b"DIPSAUS_ED25519_BATCH_V1\x00"

def verify_ed25519_batch(batch_digest, signature, public_key_pem):
    base = {**BLOCKED, "status": "ED25519_RESEARCH_BLOCKED",
            "independently_attested": False}
    if (not isinstance(batch_digest, str) or HEX.fullmatch(batch_digest) is None
            or not isinstance(signature, bytes) or len(signature) != 64
            or not isinstance(public_key_pem, bytes)
            or not 40 <= len(public_key_pem) <= 4096
            or not public_key_pem.startswith(b"-----BEGIN PUBLIC KEY-----")):
        return {**base, "reason": "INVALID_CRYPTO_INPUT"}
    try:
        with tempfile.TemporaryDirectory(prefix="dipsaus-ed25519-") as folder:
            root = Path(folder)
            (root / "pub.pem").write_bytes(public_key_pem)
            (root / "sig.bin").write_bytes(signature)
            (root / "msg.bin").write_bytes(DOMAIN + bytes.fromhex(batch_digest))
            proc = subprocess.run(
                ["openssl", "pkeyutl", "-verify", "-pubin", "-inkey",
                 str(root / "pub.pem"), "-sigfile", str(root / "sig.bin"),
                 "-rawin", "-in", str(root / "msg.bin")],
                capture_output=True, timeout=5, check=False)
        return {**BLOCKED, "status": "ED25519_SIGNATURE_VALID" if proc.returncode == 0
                else "ED25519_SIGNATURE_INVALID",
                "cryptographic_signature_valid": proc.returncode == 0,
                "independently_attested": False,
                "note": "Public key trust, custody, timing and archive completeness unverified."}
    except (OSError, subprocess.TimeoutExpired):
        return {**base, "reason": "CRYPTO_VERIFIER_UNAVAILABLE"}
