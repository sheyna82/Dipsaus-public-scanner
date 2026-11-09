"""Immutable research-only capture of an explicitly supplied Nasdaq EOD URL.

This captures source bytes and HTTP metadata without guessing an EOD parser,
index identity or a closing value. Reviewers must separately establish that
the endpoint and its dated field are genuinely issuer-provided.
"""
import base64
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED_HOSTS = {"indexes.nasdaqomx.com", "beta.indexes.nasdaqomx.com"}
MAX_BYTES = 2_000_000

class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("REDIRECT_FORBIDDEN")

def capture(url, destination, fetch=None):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS
            or parsed.username or parsed.password or parsed.fragment
            or parsed.port not in (None, 443)):
        raise ValueError("SOURCE_URL_NOT_ALLOWED")
    output = Path(destination)
    if output.exists():
        raise FileExistsError("IMMUTABLE_CAPTURE_EXISTS")
    if not output.parent.is_dir():
        raise ValueError("DESTINATION_PARENT_MISSING")
    opener = fetch or urllib.request.build_opener(NoRedirects()).open
    request = urllib.request.Request(url, headers={
        "Accept": "application/json,text/html;q=0.9,*/*;q=0.1",
        "User-Agent": "DipsausIssuerResearchCapture/1.0"})
    with opener(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError("SOURCE_HTTP_STATUS_INVALID")
        final_url = response.geturl()
        if final_url != url:
            raise ValueError("SOURCE_URL_CHANGED")
        content_type = response.headers.get("Content-Type", "")
        raw = response.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("SOURCE_BYTES_INVALID")
    receipt = {
        "schema": "dipsaus_omxh25_issuer_raw_capture_v1",
        "source_url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": 200, "content_type": content_type,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_raw_base64": base64.b64encode(raw).decode("ascii"),
        "source_authenticity_independently_verified": False,
        "official_eod_field_extracted": False, "benchmark_identity_verified": False,
        "research_only": True, "trade_ready": False,
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    return {"status": "raw_issuer_candidate_captured_unverified",
            "source_sha256": receipt["source_sha256"], "bytes": len(raw),
            "trade_ready": False}

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: python research_capture_omxh25_issuer_raw.py HTTPS_URL OUTPUT_JSON")
    print(json.dumps(capture(sys.argv[1], sys.argv[2]), sort_keys=True))
