"""Offline evidence byte-integrity gate; never grants source authority or trading rights.

Caller-supplied metadata is not independent provenance. This only checks that
the supplied bytes match the supplied SHA-256 digest and declared byte count.
"""
import hashlib
import hmac


def verify_evidence_artifact_bytes(data, declared_sha256, declared_size):
    result = {
        "status": "BLOCKED", "artifact_bytes_match_declaration": False,
        "source_attested": False, "instrument_segment_verified": False,
        "broker_route_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    if not isinstance(data, bytes) or not data:
        result["blocks"].append("NONEMPTY_ARTIFACT_BYTES_REQUIRED")
        return result
    if not isinstance(declared_size, int) or isinstance(declared_size, bool) or declared_size <= 0:
        result["blocks"].append("VALID_DECLARED_BYTE_COUNT_REQUIRED")
        return result
    if len(data) != declared_size:
        result["blocks"].append("ARTIFACT_BYTE_COUNT_MISMATCH")
        return result
    if (not isinstance(declared_sha256, str) or len(declared_sha256) != 64
            or any(c not in "0123456789abcdefABCDEF" for c in declared_sha256)):
        result["blocks"].append("VALID_DECLARED_SHA256_REQUIRED")
        return result
    actual = hashlib.sha256(data).hexdigest()
    if not hmac.compare_digest(actual, declared_sha256.lower()):
        result["blocks"].append("ARTIFACT_SHA256_MISMATCH")
        return result
    result["artifact_bytes_match_declaration"] = True
    result["byte_count"] = len(data)
    result["blocks"].append("BYTE_INTEGRITY_NOT_INDEPENDENT_SOURCE_ATTESTATION")
    return result
