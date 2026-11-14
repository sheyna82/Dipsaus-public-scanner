"""Offline-testable, explicitly approved Xetra second-request research transport.

No redirect following, automatic URL approval, source attestation, or trading.
The caller must provide a separately reviewed exact URL allowlist.
"""
import hashlib
import socket
import ssl
import urllib.error
import urllib.request

from research.spoor2_xetra_artifact_retrieval_20261113 import MAX_BYTES, NoRedirect
from research.spoor2_xetra_redirect_policy_20261114 import assess_xetra_redirect


def fetch_approved_second_request(kind, location, approved_exact_urls=(), opener=None):
    """Fetch bounded bytes only for an exact reviewed URL; always fail closed."""
    result = {
        "status": "BLOCKED", "kind": kind if isinstance(kind, str) else None,
        "source_attested": False, "instrument_segment_verified": False,
        "broker_route_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "bytes": None, "byte_count": None,
        "sha256": None, "http_status": None, "blocks": [],
    }
    policy = assess_xetra_redirect(kind, location, approved_exact_urls)
    if not policy["eligible_for_manual_second_request"]:
        result["blocks"] = list(policy["blocks"])
        return result
    # Always use a no-redirect opener in production; injected opener is for
    # isolated tests. The final URL and response status are checked regardless.
    transport = opener if opener is not None else urllib.request.build_opener(NoRedirect())
    try:
        request = urllib.request.Request(
            location, headers={"User-Agent": "DIPSAUS-research-source-audit/1.0"}
        )
        with transport.open(request, timeout=15) as response:
            result["http_status"] = response.status
            if response.status != 200 or response.geturl() != location:
                result["blocks"].append("SECOND_REQUEST_URL_OR_STATUS_MISMATCH")
                return result
            declared = response.headers.get("Content-Length")
            if declared is not None and (
                not declared.isdecimal() or int(declared) > MAX_BYTES
            ):
                result["blocks"].append("SECOND_REQUEST_SIZE_LIMIT")
                return result
            chunks, count = [], 0
            while True:
                chunk = response.read(min(65536, MAX_BYTES + 1 - count))
                if not chunk:
                    break
                count += len(chunk)
                if count > MAX_BYTES:
                    result["blocks"].append("SECOND_REQUEST_SIZE_LIMIT")
                    return result
                chunks.append(chunk)
            data = b"".join(chunks)
            if not data:
                result["blocks"].append("EMPTY_SECOND_REQUEST")
                return result
            if declared is not None and len(data) != int(declared):
                result["blocks"].append("SECOND_REQUEST_LENGTH_MISMATCH")
                return result
            result.update(bytes=data, byte_count=len(data),
                          sha256=hashlib.sha256(data).hexdigest())
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
        result["blocks"].append("SECOND_REQUEST_HTTP_ERROR")
        return result
    except (TimeoutError, socket.timeout, ssl.SSLError, urllib.error.URLError,
            OSError, ValueError):
        result["blocks"].append("SECOND_REQUEST_TRANSPORT_ERROR")
        return result
    result["blocks"].append("SECOND_REQUEST_BYTES_REQUIRE_INDEPENDENT_ATTESTATION")
    return result
