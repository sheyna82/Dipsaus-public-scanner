"""Research-only SEC source retrieval with bounded HTTPS and explicit receipt.

This tool does not establish that a filing was publicly available at a
historical entry time. No trading, notifications or operational integration.
Requires caller-provided descriptive SEC-compliant User-Agent.
"""
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

MAX_SOURCE_BYTES = 12 * 1024 * 1024


def retrieve_sec_complete_submission(source_url, user_agent, max_bytes=MAX_SOURCE_BYTES):
    if not isinstance(source_url, str):
        raise ValueError("INVALID_SEC_SOURCE_URL")
    parsed = urlsplit(source_url)
    if (parsed.scheme != "https" or parsed.netloc != "www.sec.gov"
            or parsed.query or parsed.fragment
            or not parsed.path.startswith("/Archives/edgar/data/")
            or not parsed.path.endswith(".txt")):
        raise ValueError("INVALID_SEC_SOURCE_URL")
    if (not isinstance(user_agent, str) or len(user_agent.strip()) < 12
            or "\n" in user_agent or "\r" in user_agent):
        raise ValueError("SEC_IDENTIFYING_USER_AGENT_REQUIRED")
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_SOURCE_BYTES:
        raise ValueError("INVALID_SEC_SOURCE_SIZE_LIMIT")
    request = Request(source_url, headers={
        "User-Agent": user_agent,
        "Accept": "text/plain",
        "Accept-Encoding": "identity",
    })
    # Redirects are intentionally refused; never follow to an arbitrary host.
    from urllib.request import build_opener, HTTPHandler, HTTPSHandler, HTTPRedirectHandler
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = build_opener(HTTPHandler(), HTTPSHandler(), NoRedirect())
    with opener.open(request, timeout=15) as response:
        if response.status != 200 or response.geturl() != source_url:
            raise ValueError("SEC_SOURCE_UNEXPECTED_RESPONSE")
        raw = response.read(max_bytes + 1)
    if not raw or len(raw) > max_bytes:
        raise ValueError("SEC_SOURCE_EMPTY_OR_OVERSIZED")
    receipt = {
        "schema": "sec_live_retrieval_receipt_v1",
        "source_url": source_url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "byte_count": len(raw),
        "retrieval_is_historical_publication_proof": False,
        "historical_publication_independently_proven": False,
        "eligible_for_performance_claim": False,
        "trade_ready": False,
    }
    return raw, receipt
