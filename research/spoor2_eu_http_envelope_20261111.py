"""Offline HTTP capture-envelope validation for isolated EU research.

Accepts a caller-supplied HTTP response snapshot; NEVER performs network I/O.
Headers, status, final URL and TLS claims are untrusted unless independently
recorded by an approved fetcher. Does not authorize trading.
"""
from datetime import datetime
from research.spoor2_eu_external_capture_20261111 import audit_external_capture

def review_http_capture_envelope(record, raw_bytes, *, now_utc):
    base = {"status": "BLOCKED", "trade_ready": False,
            "order_placement_enabled": False, "http_origin_attested": False}
    if not isinstance(record, dict):
        return {**base, "blocks": ["HTTP_ENVELOPE_INVALID"]}
    capture = audit_external_capture(record, raw_bytes, now_utc=now_utc)
    blocks = list(capture["blocks"])
    if capture["status"] != "CAPTURE_BYTES_MATCH_UNATTESTED":
        return {**base, "blocks": blocks, "capture_audit": capture}
    if type(record.get("http_status")) is not int or record["http_status"] != 200:
        blocks.append("HTTP_STATUS_NOT_OK")
    if record.get("request_method") != "GET":
        blocks.append("HTTP_METHOD_NOT_READ_ONLY_GET")
    if record.get("redirect_count") != 0:
        blocks.append("HTTP_REDIRECTS_NOT_ALLOWED")
    if record.get("final_url") != record.get("source_url"):
        blocks.append("HTTP_FINAL_URL_MISMATCH")
    if record.get("transport") != "https":
        blocks.append("HTTP_TRANSPORT_UNATTESTED")
    headers = record.get("response_headers")
    if not isinstance(headers, dict):
        blocks.append("HTTP_HEADERS_MISSING")
    else:
        if any(not isinstance(k, str) or not isinstance(v, str)
               or "\r" in k or "\n" in k or "\r" in v or "\n" in v
               for k, v in headers.items()):
            blocks.append("HTTP_HEADERS_INVALID")
    if len(raw_bytes) > 2_000_000:
        blocks.append("HTTP_RESPONSE_TOO_LARGE")
    blocks.append("TRUSTED_HTTP_FETCHER_NOT_CONNECTED")
    return {**base, "status": "HTTP_ENVELOPE_REVIEW_ONLY" if len(blocks) == 2 else "BLOCKED",
            "blocks": list(dict.fromkeys(blocks)), "capture_audit": capture,
            "scope": "untrusted supplied HTTP metadata; no actual request or TLS validation"}
