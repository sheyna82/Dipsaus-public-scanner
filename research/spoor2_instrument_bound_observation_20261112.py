"""Offline Ed25519 binding of identity, observation time and challenge.

A valid signature proves only possession of the supplied signing key. Neither
trusted nonce issuance nor single-use enforcement nor signer authority exists.
"""
import base64
import hashlib
import json
from research.spoor2_instrument_observation_window_20261112 import (
    audit_instrument_observation_window,
)
from research.spoor2_instrument_source_attestation_20261112 import (
    audit_instrument_source_attestation,
)

_FIELDS = frozenset(("symbol", "market", "venue_mic", "isin",
                     "observed_utc", "challenge_nonce"))


def verify_bound_instrument_observation(candidate, signed_record, signature_b64,
                                        signer_public_key_b64, *,
                                        verification_utc, max_age_seconds=300):
    base = {"status": "BLOCKED", "signature_verified": False,
            "source_attested": False, "freshness_attested": False,
            "replay_prevented": False, "trade_ready": False,
            "order_placement_enabled": False}
    if not isinstance(candidate, dict) or not isinstance(signed_record, dict):
        return {**base, "blocks": ["INVALID_BOUND_INSTRUMENT_RECORD"]}
    if set(signed_record) != _FIELDS or any(
        not isinstance(signed_record.get(k), str) or
        signed_record[k] != candidate.get(k)
        for k in ("symbol", "market", "venue_mic", "isin")
    ):
        return {**base, "blocks": ["BOUND_INSTRUMENT_IDENTITY_MISMATCH"]}
    if any(len(signed_record[k]) > 256
           for k in ("symbol", "market", "venue_mic", "isin")):
        return {**base, "blocks": ["BOUND_INSTRUMENT_RECORD_OVERSIZED"]}
    if any(isinstance(signed_record.get(k), str) and len(signed_record[k]) > 128
           for k in ("observed_utc", "challenge_nonce")):
        return {**base, "blocks": ["BOUND_INSTRUMENT_RECORD_OVERSIZED"]}
    window = audit_instrument_observation_window(
        signed_record["observed_utc"], verification_utc,
        signed_record["challenge_nonce"], max_age_seconds=max_age_seconds)
    if window["status"] != "TIME_WINDOW_CLAIMS_CONSISTENT_ONLY":
        return {**base, "blocks": window["blocks"]}
    # Reject oversized base64 before decoding or allocating signature buffers.
    if (isinstance(signature_b64, str) and len(signature_b64) > 88 or
            isinstance(signer_public_key_b64, str) and
            len(signer_public_key_b64) > 44):
        return {**base, "blocks": ["BOUND_INSTRUMENT_CRYPTO_INPUT_OVERSIZED"]}
    if not isinstance(signature_b64, str) or not isinstance(signer_public_key_b64, str):
        return {**base, "blocks": ["INVALID_BOUND_INSTRUMENT_SIGNATURE_ENCODING"]}
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        key = base64.b64decode(signer_public_key_b64, validate=True)
        if (base64.b64encode(signature).decode("ascii") != signature_b64 or
                base64.b64encode(key).decode("ascii") != signer_public_key_b64):
            raise ValueError("noncanonical base64")
        if len(signature) != 64 or len(key) != 32:
            raise ValueError("wrong length")
    except (ValueError, base64.binascii.Error):
        return {**base, "blocks": ["INVALID_BOUND_INSTRUMENT_SIGNATURE_ENCODING"]}
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        return {**base, "blocks": ["BOUND_INSTRUMENT_CRYPTO_UNAVAILABLE"]}
    payload = json.dumps(signed_record, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode("ascii")
    try:
        Ed25519PublicKey.from_public_bytes(key).verify(signature, payload)
    except (InvalidSignature, ValueError):
        return {**base, "blocks": ["BOUND_INSTRUMENT_SIGNATURE_INVALID"]}
    admission = audit_instrument_source_attestation(
        {"signer_public_key_b64": signer_public_key_b64})
    return {**base, "status": "BOUND_SIGNATURE_VALID_UNATTESTED",
            "signature_verified": True,
            "record_sha256": hashlib.sha256(payload).hexdigest(),
            "blocks": admission["blocks"] + [
                "INSTRUMENT_CHALLENGE_ISSUANCE_NOT_ATTESTED",
                "INSTRUMENT_NONCE_SINGLE_USE_NOT_ENFORCED",
                "INSTRUMENT_TRUSTED_CLOCK_NOT_ATTESTED",
                "INSTRUMENT_SOURCE_INDEPENDENCE_NOT_ATTESTED"]}
