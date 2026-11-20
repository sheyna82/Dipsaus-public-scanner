"""Offline HMAC-SHA256 integrity experiment with synthetic-only secrets.

HMAC is symmetric authentication, NOT a public-key digital signature.
The caller supplies the key and reference; this cannot prove independent
key custody, trusted time, source authenticity, or archive completeness.
"""
import hashlib
import hmac
import re

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False,
           "archive_integrity_independently_verified": False}
HEX = re.compile(r"[0-9a-f]{64}\Z")
DOMAIN = b"DIPSAUS_SYNTHETIC_BATCH_HMAC_V1\x00"

def _valid_digest(digest):
    return isinstance(digest, str) and HEX.fullmatch(digest) is not None

def synthetic_mac(batch_digest, *, synthetic_key):
    if (not _valid_digest(batch_digest) or not isinstance(synthetic_key, bytes)
            or len(synthetic_key) < 32):
        return {**BLOCKED, "status": "SYNTHETIC_MAC_BLOCKED",
                "reason": "INVALID_DIGEST_OR_KEY"}
    tag = hmac.new(synthetic_key, DOMAIN + bytes.fromhex(batch_digest),
                   hashlib.sha256).hexdigest()
    return {**BLOCKED, "status": "SYNTHETIC_MAC_GENERATED",
            "tag": tag, "independently_authenticated": False}

def verify_synthetic_mac(batch_digest, tag, *, synthetic_key):
    if not _valid_digest(tag):
        return {**BLOCKED, "status": "SYNTHETIC_MAC_BLOCKED",
                "reason": "INVALID_TAG"}
    computed = synthetic_mac(batch_digest, synthetic_key=synthetic_key)
    if computed["status"] != "SYNTHETIC_MAC_GENERATED":
        return computed
    match = hmac.compare_digest(computed["tag"], tag)
    return {**BLOCKED, "status": "SYNTHETIC_MAC_MATCH" if match
            else "SYNTHETIC_MAC_MISMATCH", "tag_matches": match,
            "independently_authenticated": False,
            "note": "A shared caller-provided key cannot establish independent attestation."}
