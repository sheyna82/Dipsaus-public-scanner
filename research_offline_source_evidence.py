"""Offline-only source-byte evidence preparation. No DNS, HTTP, or sockets.

Caller-provided bytes and timestamps are not independently authenticated.
"""
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlsplit


def prepare_offline_source_evidence(url, *, source_bytes, captured_at_utc,
                                    allowed_hosts, max_bytes=1_000_000):
    if not isinstance(url, str):
        raise ValueError("invalid_https_source_url")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid_https_source_url") from exc
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.fragment or parsed.query or port not in (None, 443)):
        raise ValueError("invalid_https_source_url")
    host = parsed.hostname
    if (not isinstance(allowed_hosts, (set, frozenset)) or not allowed_hosts
            or host not in allowed_hosts or host == "localhost"
            or host.endswith(".local")):
        raise ValueError("source_host_not_allowlisted")
    if (not isinstance(max_bytes, int) or isinstance(max_bytes, bool)
            or not 0 < max_bytes <= 5_000_000):
        raise ValueError("invalid_capture_limit")
    if (not isinstance(source_bytes, bytes) or not source_bytes
            or len(source_bytes) > max_bytes):
        raise ValueError("invalid_source_response_size")
    if (not isinstance(captured_at_utc, datetime)
            or captured_at_utc.tzinfo is None
            or captured_at_utc.utcoffset() != timezone.utc.utcoffset(captured_at_utc)):
        raise ValueError("capture_clock_must_be_utc")
    return {
        "source_url": url,
        "source_bytes": source_bytes,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_captured_at_utc": captured_at_utc.isoformat().replace("+00:00", "Z"),
        "source_http_status": None,
        "independent_source_authentication": False,
        "independent_timestamp_proof": False,
        "trade_ready": False,
        "research_only": True,
        "offline_supplied_bytes": True,
    }
