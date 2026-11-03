"""Read-only HTTPS capture for research-only market-source observations.

A successful HTTPS fetch is NOT independent market-data authentication or proof
that a trading signal was registered before its outcome. No live integration.
"""
import hashlib
import ipaddress
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPSHandler, HTTPRedirectHandler
from urllib.error import HTTPError, URLError


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirects_not_supported_for_research_capture")


def capture_public_https_source(url, *, clock, allowed_hosts, opener=None, max_bytes=1_000_000):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("invalid_https_source_url")
    if parsed.port not in (None, 443):
        raise ValueError("nonstandard_https_port")
    host = parsed.hostname
    if not isinstance(allowed_hosts, (set, frozenset)) or not allowed_hosts or host not in allowed_hosts:
        raise ValueError("source_host_not_allowlisted")
    if host.lower() == "localhost" or host.endswith(".local"):
        raise ValueError("nonpublic_source_host")
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("source_dns_resolution_failed") from exc
    if not addresses or any(not ipaddress.ip_address(info[4][0]).is_global for info in addresses):
        raise ValueError("nonpublic_source_address")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 0 < max_bytes <= 5_000_000:
        raise ValueError("invalid_capture_limit")
    # Fail closed: DNS validation and the HTTPS connection are not pinned to the\n    # same IP. A later DNS answer could differ (DNS rebinding / TOCTOU).\n    # Until connection-level IP pinning is implemented and audited, this\n    # module accepts only an explicitly injected transport for offline tests.\n    if opener is None:\n        raise ValueError("live_https_transport_disabled_pending_dns_pinning")
    request = Request(url, headers={"User-Agent": "DIPSAUS-research-evidence/1.0", "Accept": "application/json,text/csv,text/plain"})
    try:
        with opener.open(request, timeout=15) as response:
            final_url = response.geturl()
            if final_url != url:
                raise ValueError("redirects_not_supported_for_research_capture")
            status = response.status
            if status != 200:
                raise ValueError("unexpected_source_http_status")
            raw = response.read(max_bytes + 1)
            if not raw or len(raw) > max_bytes:
                raise ValueError("invalid_source_response_size")
            captured = clock()
    except (HTTPError, URLError) as exc:
        raise ValueError("source_fetch_failed") from exc
    if not isinstance(captured, datetime) or captured.tzinfo is None or captured.utcoffset() != timezone.utc.utcoffset(captured):
        raise ValueError("capture_clock_must_be_utc")
    return {
        "source_url": url,
        "source_bytes": raw,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_captured_at_utc": captured.isoformat().replace("+00:00", "Z"),
        "source_http_status": status,
        "independent_source_authentication": False,
        "independent_timestamp_proof": False,
        "trade_ready": False,
        "research_only": True,
    }
