"""Offline synthetic key-rotation policy for historical attestations.

Policy metadata is caller-supplied, not independently trusted. A passing
result does not verify signatures, key custody or a trusted timestamp.
"""
from datetime import datetime, timezone
import hashlib
import re

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}
HEX = re.compile(r"[0-9a-f]{64}\Z")
KEY_FIELDS = {"key_id", "public_key_pem", "valid_from_utc", "valid_until_utc",
              "revoked_from_utc"}

def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except ValueError:
        return None

def assess_key_rotation(keys, *, key_id, attested_utc, expected_public_key_sha256):
    base = {**BLOCKED, "status": "KEY_POLICY_BLOCKED",
            "independently_trusted_key": False}
    if (not isinstance(keys, list) or not isinstance(key_id, str)
            or not isinstance(expected_public_key_sha256, str)
            or HEX.fullmatch(expected_public_key_sha256) is None):
        return {**base, "reason": "INVALID_INPUT"}
    at = _utc(attested_utc)
    if at is None:
        return {**base, "reason": "INVALID_ATTESTATION_TIME"}
    seen = set()
    selected = None
    for item in keys:
        if not isinstance(item, dict) or set(item) != KEY_FIELDS:
            return {**base, "reason": "INVALID_KEY_RECORD"}
        kid = item["key_id"]
        if not isinstance(kid, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,32}", kid) or kid in seen:
            return {**base, "reason": "DUPLICATE_OR_INVALID_KEY_ID"}
        seen.add(kid)
        pem = item["public_key_pem"]
        if not isinstance(pem, bytes) or not pem.startswith(b"-----BEGIN PUBLIC KEY-----") or len(pem) > 4096:
            return {**base, "reason": "INVALID_PUBLIC_KEY"}
        start = _utc(item["valid_from_utc"])
        end = _utc(item["valid_until_utc"])
        revoked = _utc(item["revoked_from_utc"]) if item["revoked_from_utc"] is not None else None
        if start is None or end is None or start >= end or (
                item["revoked_from_utc"] is not None and revoked is None):
            return {**base, "reason": "INVALID_KEY_WINDOW"}
        if kid == key_id:
            selected = (pem, start, end, revoked)
    if selected is None:
        return {**base, "reason": "UNKNOWN_KEY"}
    pem, start, end, revoked = selected
    if hashlib.sha256(pem).hexdigest() != expected_public_key_sha256:
        return {**base, "reason": "KEY_FINGERPRINT_MISMATCH"}
    if not start <= at < end:
        return {**base, "reason": "KEY_NOT_VALID_AT_ATTESTATION"}
    if revoked is not None and at >= revoked:
        return {**base, "reason": "KEY_REVOKED_AT_ATTESTATION"}
    return {**BLOCKED, "status": "KEY_POLICY_STRUCTURALLY_ACCEPTED",
            "independently_trusted_key": False,
            "note": "Untrusted key registry and timestamp; no independent key attestation."}
