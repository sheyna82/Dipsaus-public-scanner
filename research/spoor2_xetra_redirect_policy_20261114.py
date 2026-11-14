"""Explicit opt-in redirect policy for official Xetra research artifacts.

The allowlist must be populated from independently reviewed exact URLs.
No automatic redirects, wildcard hosts, query parameters, or broker privileges.
"""
import re
from urllib.parse import urlsplit
from research.spoor2_xetra_artifact_retrieval_20261113 import SOURCES

def assess_xetra_redirect(kind, location, approved_exact_urls=()):
    result = {
        "status": "BLOCKED", "kind": kind if isinstance(kind, str) else None, "eligible_for_manual_second_request": False,
        "source_attested": False, "instrument_segment_verified": False,
        "broker_route_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    if not isinstance(kind, str) or kind not in SOURCES:
        result["blocks"].append("UNKNOWN_XETRA_ARTIFACT")
        return result
    if not isinstance(location, str) or not isinstance(approved_exact_urls, (tuple, frozenset)):
        result["blocks"].append("INVALID_REDIRECT_POLICY_INPUT")
        return result
    try:
        source = urlsplit(SOURCES[kind])
        target = urlsplit(location)
        target_port = target.port
    except ValueError:
        result["blocks"].append("MALFORMED_REDIRECT_TARGET")
        return result
    if (target.scheme != "https" or target.netloc != source.netloc
            or target.username is not None or target.password is not None
            or target_port is not None or target.query or target.fragment
            or not target.path.startswith("/resource/blob/")
            or any(segment in (".", "..") for segment in target.path.split("/"))
            or "%" in target.path or "\\" in target.path):
        result["blocks"].append("REDIRECT_TARGET_NOT_OFFICIAL_OR_UNSAFE")
        return result
    if location not in approved_exact_urls or location == SOURCES[kind]:
        result["blocks"].append("REDIRECT_NOT_EXPLICITLY_APPROVED")
        return result
    result["eligible_for_manual_second_request"] = True
    result["blocks"].append("MANUAL_SECOND_REQUEST_REQUIRES_BOUNDED_NO_REDIRECT_FETCH_AND_BYTE_REVIEW")
    return result
