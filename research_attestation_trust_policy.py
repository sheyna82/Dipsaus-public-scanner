"""Offline trust-policy gate for independently verified attestations.

Does not verify cryptographic signatures. Accepts only a verifier result
provided by a separate trusted boundary; supplied claims are never enough.
"""
import re
from datetime import datetime, timezone

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "archive_integrity_independently_verified": False,
           "source_authenticity_independently_verified": False}
HEX = re.compile(r"[0-9a-f]{64}\Z")
FIELDS = {"batch_digest", "key_id", "verification_utc", "signature_valid",
          "key_revoked", "trusted_verifier", "reference_digest"}

def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except ValueError:
        return None

def assess_verifier_evidence(evidence, *, trusted_key_ids):
    base = {**BLOCKED, "status": "ATTESTATION_TRUST_BLOCKED",
            "independent_signature_verified": False}
    if (not isinstance(evidence, dict) or set(evidence) != FIELDS
            or not isinstance(trusted_key_ids, (tuple, frozenset))
            or any(not isinstance(k, str) for k in trusted_key_ids)):
        return {**base, "reason": "INVALID_VERIFIER_INPUT"}
    for key in ("batch_digest", "reference_digest"):
        value = evidence[key]
        if not isinstance(value, str) or HEX.fullmatch(value) is None:
            return {**base, "reason": "INVALID_DIGEST"}
    if evidence["batch_digest"] != evidence["reference_digest"]:
        return {**base, "reason": "REFERENCE_DIGEST_MISMATCH"}
    if evidence["key_id"] not in trusted_key_ids:
        return {**base, "reason": "UNTRUSTED_KEY"}
    if evidence["key_revoked"] is not False:
        return {**base, "reason": "KEY_REVOKED_OR_UNKNOWN"}
    if evidence["signature_valid"] is not True:
        return {**base, "reason": "SIGNATURE_INVALID_OR_UNKNOWN"}
    if evidence["trusted_verifier"] is not True:
        return {**base, "reason": "UNTRUSTED_VERIFIER"}
    if _utc(evidence["verification_utc"]) is None:
        return {**base, "reason": "INVALID_VERIFICATION_TIME"}
    return {**BLOCKED, "status": "ATTESTATION_CLAIMS_STRUCTURALLY_ACCEPTED",
            "independent_signature_verified": False,
            "note": "Caller-controlled claims cannot establish a trusted verification boundary."}
