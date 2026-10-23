"""Offline historical source manifest audit. No downloads or trust assertions."""
import hashlib
from datetime import datetime


def audit_historical_source_manifest(manifest, payload):
    """Verify immutable byte identity and explicit acquisition metadata.

    A matching hash proves consistency with the supplied manifest, not that
    the provider, publication time, or license claims are authentic.
    """
    if not isinstance(manifest, dict) or not isinstance(payload, bytes):
        raise ValueError("invalid_manifest_input")
    required = ("provider", "dataset", "source_url", "license_reference",
                "retrieved_at", "sha256", "adjustment_policy",
                "universe_policy")
    if any(not isinstance(manifest.get(key), str) or
           not manifest[key].strip() for key in required):
        raise ValueError("incomplete_manifest")
    try:
        timestamp = datetime.fromisoformat(manifest["retrieved_at"])
    except ValueError as exc:
        raise ValueError("invalid_retrieval_time") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timezone_required")
    published_raw = manifest.get("published_at")
    if published_raw is not None:
        if not isinstance(published_raw, str):
            raise ValueError("invalid_publication_time")
        try:
            published = datetime.fromisoformat(published_raw)
        except ValueError as exc:
            raise ValueError("invalid_publication_time") from exc
        if published.tzinfo is None or published.utcoffset() is None:
            raise ValueError("publication_timezone_required")
        if published > timestamp:
            raise ValueError("publication_after_retrieval")
    if len(manifest["sha256"]) != 64 or any(
            character not in "0123456789abcdef" for character in manifest["sha256"]):
        raise ValueError("invalid_sha256")
    actual = hashlib.sha256(payload).hexdigest()
    if actual != manifest["sha256"]:
        raise ValueError("payload_hash_mismatch")
    return {
        "accepted": True,
        "payload_sha256": actual,
        "bytes": len(payload),
        "manifest_consistent": True,
        "license_verified": False,
        "provider_authenticity_verified": False,
        "point_in_time_verified": False,
        "publication_time_structurally_valid": published_raw is not None,
        "publication_time_authenticity_verified": False,
        "trade_ready": False,
    }
