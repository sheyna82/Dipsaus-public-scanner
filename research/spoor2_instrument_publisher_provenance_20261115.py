"""Offline publisher provenance inventory; never source attestation.

Caller-supplied URLs, issuer labels and retrieval timestamps are declarations.
HTTPS and host agreement cannot prove that bytes came from an official publisher.
No requests, redirects, DNS, broker calls, or execution.
"""
from datetime import datetime, timezone
from urllib.parse import urlsplit


def inspect_publisher_provenance(record):
    result = {
        "status": "BLOCKED", "publisher_metadata_well_formed": False,
        "publisher_identity_verified": False,
        "independent_source_authority_verified": False,
        "source_attested": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    if not isinstance(record, dict):
        result["blocks"].append("PUBLISHER_PROVENANCE_REQUIRED")
        return result
    publisher = record.get("publisher_id")
    url = record.get("retrieval_url")
    captured = record.get("retrieved_at_utc")
    if not isinstance(publisher, str) or not publisher.strip() or publisher != publisher.strip() or len(publisher) > 128:
        result["blocks"].append("INVALID_PUBLISHER_ID")
        return result
    if not isinstance(url, str) or len(url) > 2048 or any(ord(c) < 33 or ord(c) == 127 for c in url):
        result["blocks"].append("INVALID_RETRIEVAL_URL")
        return result
    try:
        parts = urlsplit(url)
        if (parts.scheme != "https" or not parts.hostname or parts.username is not None
                or parts.password is not None or parts.fragment or parts.port not in (None, 443)
                or not parts.netloc.isascii() or parts.hostname.endswith(".")
                or parts.hostname.startswith(".") or ".." in parts.hostname):
            raise ValueError("invalid URL")
    except ValueError:
        result["blocks"].append("INVALID_RETRIEVAL_URL")
        return result
    if not isinstance(captured, str):
        result["blocks"].append("INVALID_RETRIEVAL_TIMESTAMP")
        return result
    try:
        instant = datetime.fromisoformat(captured)
        if instant.tzinfo is None or instant.utcoffset() != timezone.utc.utcoffset(instant):
            raise ValueError("not UTC")
    except ValueError:
        result["blocks"].append("INVALID_RETRIEVAL_TIMESTAMP")
        return result
    result["publisher_metadata_well_formed"] = True
    result["blocks"].append("PUBLISHER_IDENTITY_NOT_INDEPENDENTLY_VERIFIED")
    return result
