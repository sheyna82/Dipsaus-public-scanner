"""Offline provenance gate for official MIC and exchange file snapshots.

This validates an explicitly approved retrieval transcript, not TLS, actual
network responses, publisher authenticity or instrument trading eligibility.
No network requests or redirect following are performed here.
"""
import hashlib
from urllib.parse import urlsplit

BLOCKED = {"status": "OFFICIAL_SOURCE_BLOCKED", "trade_ready": False,
           "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}

def assess_official_snapshot(*, body, source_url, approved_url, response_status,
                             redirect_location=None, expected_sha256=None):
    if not isinstance(source_url, str) or not isinstance(approved_url, str):
        return {**BLOCKED, "reason": "INVALID_URL"}
    try:
        actual, approved = urlsplit(source_url), urlsplit(approved_url)
        if any(p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment for p in (actual, approved)):
            return {**BLOCKED, "reason": "UNSAFE_URL"}
    except ValueError:
        return {**BLOCKED, "reason": "UNSAFE_URL"}
    if source_url != approved_url:
        return {**BLOCKED, "reason": "UNAPPROVED_SOURCE_URL"}
    if type(response_status) is not int or response_status != 200:
        return {**BLOCKED, "reason": "HTTP_STATUS_NOT_OK"}
    if redirect_location is not None:
        return {**BLOCKED, "reason": "REDIRECT_NOT_APPROVED"}
    if not isinstance(body, bytes) or not body:
        return {**BLOCKED, "reason": "EMPTY_OR_INVALID_BODY"}
    digest = hashlib.sha256(body).hexdigest()
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or digest != expected_sha256:
        return {**BLOCKED, "reason": "DIGEST_NOT_ATTESTED"}
    return {"status": "OFFLINE_SNAPSHOT_METADATA_CONSISTENT",
            "sha256": digest, "size_bytes": len(body),
            "source_url": source_url,
            "trade_ready": False, "order_placement_enabled": False,
            "source_authenticity_independently_verified": False,
            "note": "Caller-supplied retrieval metadata; external authenticity not established."}
