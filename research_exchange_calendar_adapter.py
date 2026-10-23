"""Offline adapter for independently supplied exchange_calendars session output.

Importing this module does not install, import, or execute any third-party code.
The upstream calendar's identity/version/source must be recorded by the caller.
"""
import hashlib
import json
from research_exchange_session_audit import audit_expected_sessions


def audit_calendar_export(price_dates, calendar_export):
    if not isinstance(calendar_export, dict):
        raise ValueError("invalid_calendar_export")
    required = ("exchange", "calendar_library", "calendar_version",
                "session_dates", "source_sha256")
    if any(not calendar_export.get(field) for field in required):
        raise ValueError("missing_calendar_provenance")
    if calendar_export["calendar_library"] not in (
            "exchange_calendars", "pandas_market_calendars"):
        raise ValueError("unsupported_calendar_library")
    digest = calendar_export["source_sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or any(
            char not in "0123456789abcdef" for char in digest):
        raise ValueError("invalid_calendar_digest")
    if calendar_export.get("digest_scope") != "canonical_session_dates_json":
        raise ValueError("unverified_calendar_digest_scope")
    if calendar_export.get("digest_scope") == "canonical_session_dates_json":
        canonical = json.dumps(calendar_export["session_dates"], separators=(",", ":"), ensure_ascii=True)
        if hashlib.sha256(canonical.encode("ascii")).hexdigest() != digest:
            raise ValueError("calendar_digest_mismatch")
    result = audit_expected_sessions(price_dates, calendar_export["session_dates"])
    result.update({"exchange": calendar_export["exchange"],
                   "calendar_library": calendar_export["calendar_library"],
                   "calendar_version": calendar_export["calendar_version"],
                   "calendar_source_sha256": digest,
                   "calendar_provenance_recorded": True,
                   "calendar_export_digest_verified": True,
                   "calendar_provenance_verified": False,
                   "trade_ready": False})
    return result
