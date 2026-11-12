"""Offline instrument-source attestation admission policy.

No signer is approved by default. Self-supplied signatures, hashes, and
'verified' flags cannot establish independently sourced instrument identity.
No network, notifications, secrets, or execution.
"""
import base64
import hashlib

APPROVED_INSTRUMENT_SIGNER_KEY_SHA256 = frozenset()


def audit_instrument_source_attestation(attestation):
    base = {"status": "BLOCKED", "source_attested": False,
            "trade_ready": False, "order_placement_enabled": False}
    if not isinstance(attestation, dict):
        return {**base, "blocks": ["INSTRUMENT_ATTESTATION_MISSING"]}
    key = attestation.get("signer_public_key_b64")
    if not isinstance(key, str):
        return {**base, "blocks": ["INSTRUMENT_SIGNER_KEY_INVALID"]}
    if len(key) > 44:
        return {**base, "blocks": ["INSTRUMENT_SIGNER_KEY_OVERSIZED"]}
    try:
        raw = base64.b64decode(key, validate=True)
    except (ValueError, base64.binascii.Error):
        return {**base, "blocks": ["INSTRUMENT_SIGNER_KEY_INVALID"]}
    if len(raw) != 32:
        return {**base, "blocks": ["INSTRUMENT_SIGNER_KEY_INVALID"]}
    fingerprint = hashlib.sha256(raw).hexdigest()
    if fingerprint not in APPROVED_INSTRUMENT_SIGNER_KEY_SHA256:
        return {**base, "blocks": ["INSTRUMENT_SIGNER_NOT_INDEPENDENTLY_APPROVED"],
                "signer_key_sha256": fingerprint}
    # Even an approved key would require an independently captured, bound,
    # time-fresh and cryptographically verified record before admission.
    return {**base, "blocks": ["INSTRUMENT_SIGNED_RECORD_VERIFIER_NOT_CONNECTED"],
            "signer_key_sha256": fingerprint}
