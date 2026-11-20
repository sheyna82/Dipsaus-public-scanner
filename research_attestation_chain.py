"""Synthetic-only verification of an independently supplied attestation chain.

No keys, signatures, external storage, private data or production integration.
A caller-supplied chain cannot establish independent authenticity.
"""
import re
from datetime import datetime, timezone

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False,
           "archive_integrity_independently_verified": False}
FIELDS = {"sequence", "batch_digest", "previous_digest", "closed_utc",
          "attested_utc", "key_id", "signature_verified_externally"}
HEX = re.compile(r"[0-9a-f]{64}\Z")

def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None

def check_attestation_chain(records, *, max_attestation_delay_seconds=3600):
    base = {**BLOCKED, "status": "ATTESTATION_CHAIN_BLOCKED",
            "attestation_independently_verified": False}
    if (not isinstance(records, list) or not records
            or type(max_attestation_delay_seconds) is not int
            or not 0 <= max_attestation_delay_seconds <= 86400):
        return {**base, "reason": "INVALID_INPUT"}
    previous = None
    last_attested = None
    for index, item in enumerate(records):
        if not isinstance(item, dict) or set(item) != FIELDS:
            return {**base, "reason": "INVALID_RECORD"}
        if type(item["sequence"]) is not int or item["sequence"] != index + 1:
            return {**base, "reason": "MISSING_DUPLICATE_OR_REORDERED_SEQUENCE"}
        digest, prior = item["batch_digest"], item["previous_digest"]
        if not isinstance(digest, str) or HEX.fullmatch(digest) is None:
            return {**base, "reason": "INVALID_BATCH_DIGEST"}
        if (prior is not None and
                (not isinstance(prior, str) or HEX.fullmatch(prior) is None)):
            return {**base, "reason": "INVALID_PREVIOUS_DIGEST"}
        if prior != previous:
            return {**base, "reason": "BROKEN_CHAIN_LINK"}
        closed, attested = _utc(item["closed_utc"]), _utc(item["attested_utc"])
        if (closed is None or attested is None or attested < closed
                or (attested - closed).total_seconds() > max_attestation_delay_seconds
                or (last_attested is not None and attested < last_attested)):
            return {**base, "reason": "INVALID_OR_LATE_ATTESTATION_TIME"}
        if not isinstance(item["key_id"], str) or not re.fullmatch(
                r"[a-zA-Z0-9_-]{1,32}", item["key_id"]):
            return {**base, "reason": "INVALID_KEY_ID"}
        # Never trust a caller's claimed external verification.
        if item["signature_verified_externally"] is not False:
            return {**base, "reason": "UNTRUSTED_VERIFICATION_CLAIM"}
        previous, last_attested = digest, attested
    return {**BLOCKED, "status": "ATTESTATION_CHAIN_STRUCTURALLY_CONSISTENT",
            "record_count": len(records), "attestation_independently_verified": False,
            "note": "Only structure checked; no signature, trusted timestamp or independent source."}
