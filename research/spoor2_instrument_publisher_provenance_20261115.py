"""Offline publisher provenance inventory; never source attestation.

Caller-supplied URLs, issuer labels and retrieval timestamps are declarations.
HTTPS and host agreement cannot prove that bytes came from an official publisher.
No requests, redirects, DNS, broker calls, or execution.
"""
from datetime import datetime, timezone
import ipaddress
from urllib.parse import urlsplit


def inspect_publisher_provenance(record):
    result = {
        "status": "BLOCKED", "publisher_metadata_well_formed": False,
        "publisher_identity_verified": False,
        "retrieval_freshness_verified": False,
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
    # Reject ambiguous authority encodings before URL parsing.
    if chr(92) in url or "@" in url:
        result["blocks"].append("INVALID_RETRIEVAL_URL")
        return result
    try:
        parts = urlsplit(url)
        if "%" in parts.netloc:
            raise ValueError("encoded authority")
        if (parts.scheme != "https" or not parts.hostname or parts.username is not None
                or parts.password is not None or parts.fragment or parts.port not in (None, 443)
                or not parts.netloc.isascii() or not parts.hostname.isascii()
                or parts.hostname.endswith(".")
                or parts.hostname.startswith(".") or ".." in parts.hostname):
            raise ValueError("invalid URL")
    except ValueError:
        result["blocks"].append("INVALID_RETRIEVAL_URL")
        return result
    try:
        ipaddress.ip_address(parts.hostname)
    except ValueError:
        pass
    else:
        result["blocks"].append("IP_LITERAL_PUBLISHER_HOST_NOT_ALLOWED")
        return result
    # A single-label host or a reserved local name cannot identify a public publisher.
    host_labels = parts.hostname.lower().split(".")
    if (len(host_labels) < 2 or any(not label or len(label) > 63
            or label[0] == "-" or label[-1] == "-"
            or any(not (c.isascii() and (c.isalnum() or c == "-")) for c in label)
            for label in host_labels)
            or host_labels[-1] in ("local", "localhost", "internal", "test", "invalid")):
        result["blocks"].append("NONPUBLIC_OR_INVALID_PUBLISHER_HOST")
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
