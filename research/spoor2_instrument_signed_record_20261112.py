"""Offline Ed25519 verification of exact instrument identity claims.

Signature validity is not independent source authority, market truth, or trade
permission. Caller-supplied keys never establish trust.
"""
import base64
import hashlib
import json
from research.spoor2_instrument_source_attestation_20261112 import (
    audit_instrument_source_attestation,
)

_FIELDS = ("symbol", "market", "venue_mic", "isin")


def verify_instrument_signed_record(candidate, signed_record, signature_b64,
                                    signer_public_key_b64):
    base = {"status": "BLOCKED", "signature_verified": False,
            "source_attested": False, "trade_ready": False,
            "order_placement_enabled": False}
    if not isinstance(candidate, dict) or not isinstance(signed_record, dict):
        return {**base, "blocks": ["INVALID_INSTRUMENT_SIGNED_RECORD"]}
    if set(signed_record) != set(_FIELDS) or any(
        not isinstance(signed_record.get(k), str) or
        signed_record[k] != candidate.get(k) for k in _FIELDS
    ):
        return {**base, "blocks": ["INSTRUMENT_SIGNED_RECORD_BINDING_MISMATCH"]}
    # Reject oversized base64 before decoding or allocating signature buffers.
    if (isinstance(signature_b64, str) and len(signature_b64) > 88 or
            isinstance(signer_public_key_b64, str) and
            len(signer_public_key_b64) > 44):
        return {**base, "blocks": ["INSTRUMENT_CRYPTO_INPUT_OVERSIZED"]}
    if any(len(signed_record.get(k, "")) > 256 for k in ("symbol", "market", "venue_mic", "isin") if isinstance(signed_record.get(k), str)):
        return {**base, "blocks": ["INSTRUMENT_SIGNED_RECORD_OVERSIZED"]}
    if not isinstance(signature_b64, str) or not isinstance(signer_public_key_b64, str):
        return {**base, "blocks": ["INVALID_INSTRUMENT_SIGNATURE_ENCODING"]}
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        key = base64.b64decode(signer_public_key_b64, validate=True)
        if (base64.b64encode(signature).decode("ascii") != signature_b64 or
                base64.b64encode(key).decode("ascii") != signer_public_key_b64):
            raise ValueError("noncanonical base64")
        if len(signature) != 64 or len(key) != 32:
            raise ValueError("invalid signature/key size")
    except (ValueError, base64.binascii.Error):
        return {**base, "blocks": ["INVALID_INSTRUMENT_SIGNATURE_ENCODING"]}
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        return {**base, "blocks": ["INSTRUMENT_CRYPTO_VERIFIER_UNAVAILABLE"]}
    payload = json.dumps(signed_record, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode("ascii")
    try:
        Ed25519PublicKey.from_public_bytes(key).verify(signature, payload)
    except (InvalidSignature, ValueError):
        return {**base, "blocks": ["INSTRUMENT_SIGNATURE_INVALID"]}
    admission = audit_instrument_source_attestation(
        {"signer_public_key_b64": signer_public_key_b64})
    return {**base, "status": "SIGNATURE_VALID_SOURCE_UNATTESTED",
            "signature_verified": True,
            "record_sha256": hashlib.sha256(payload).hexdigest(),
            "blocks": admission["blocks"] +
                      ["INSTRUMENT_SOURCE_INDEPENDENCE_NOT_ATTESTED",
                       "INSTRUMENT_RECORD_FRESHNESS_NOT_ATTESTED"]}
