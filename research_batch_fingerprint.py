"""Offline deterministic fingerprints for synthetic historical research batches.

A digest detects modifications relative to a *trusted external reference*.
It cannot authenticate its own creation or prove archive completeness.
"""
import hashlib
import json
from research_batch_manifest import reconcile_batch_manifest

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}

def fingerprint_batch(manifest, events, *, expected_digest=None):
    reconciliation = reconcile_batch_manifest(manifest, events)
    if reconciliation["status"] != "BATCH_COUNTS_MATCH_SELF_REPORTED":
        return {**BLOCKED, "status": "BATCH_FINGERPRINT_BLOCKED",
                "reason": reconciliation.get("reason", reconciliation["status"]),
                "archive_integrity_independently_verified": False}
    if expected_digest is not None and (
            not isinstance(expected_digest, str) or len(expected_digest) != 64
            or any(c not in "0123456789abcdef" for c in expected_digest)):
        return {**BLOCKED, "status": "BATCH_FINGERPRINT_BLOCKED",
                "reason": "INVALID_EXPECTED_DIGEST",
                "archive_integrity_independently_verified": False}
    # Canonical ordering is by event_id, after contract validation ensures uniqueness.
    payload = {"manifest": manifest,
               "events": sorted(events, key=lambda e: e["event_id"])}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True, allow_nan=False).encode("ascii")
    digest = hashlib.sha256(b"DIPSAUS_HISTORY_BATCH_V1\x00" + canonical).hexdigest()
    return {**BLOCKED, "status": "BATCH_FINGERPRINT_RESEARCH_ONLY",
            "sha256": digest, "matches_expected_digest": (
                digest == expected_digest if expected_digest is not None else None),
            "archive_integrity_independently_verified": False,
            "external_reference_attested": False,
            "note": "An untrusted expected digest is not independent attestation."}
