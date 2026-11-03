"""Research-only one-shot Finnhub source capture; no signals or orders.

Run manually with FINNHUB_API_KEY set in the environment. Do not print source
responses or tokens. The source is NOT independently authenticated as market
truth and its quote timestamp is NOT proof of when the signal was available.
"""
import hashlib
import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("source_redirect_forbidden")
from datetime import datetime, timezone
from pathlib import Path

ALLOWED = {"AAPL", "AMD", "COHU", "CSGP"}
MAX_RESPONSE_BYTES = 65536


def capture(symbol, destination, *, token, opener=None, clock=None):
    if symbol not in ALLOWED or not isinstance(token, str) or not token.strip():
        raise ValueError("unsupported_symbol_or_missing_token")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("observation_already_exists")
    if not destination.parent.is_dir():
        raise ValueError("observation_directory_missing")
    now = clock or (lambda: datetime.now(timezone.utc))
    started = now()
    if started.tzinfo is None or started.utcoffset().total_seconds() != 0:
        raise ValueError("utc_clock_required")
    url = "https://finnhub.io/api/v1/quote?" + urllib.parse.urlencode({"symbol": symbol})
    request = urllib.request.Request(url, headers={
        "X-Finnhub-Token": token, "Accept": "application/json",
        "User-Agent": "DipsausProspectiveResearch/1.0"})
    # Never forward the API token through an HTTP redirect.
    fetch = opener or urllib.request.build_opener(NoRedirects()).open
    with fetch(request, timeout=15) as response:
        if response.status != 200:
            raise ValueError("source_http_not_successful")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    finished = now()
    if not raw or len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("source_response_size_invalid")
    # Fail closed if a provider response unexpectedly echoes the credential.
    if token.encode("utf-8") in raw:
        raise ValueError("source_response_contains_credential")
    try:
        body = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_quote")))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("source_quote_invalid") from exc
    if not isinstance(body, dict) or not isinstance(body.get("c"), (int, float)) or not math.isfinite(body["c"]) or body["c"] <= 0:
        raise ValueError("source_quote_invalid")
    if isinstance(body["c"], bool):
        raise ValueError("source_quote_invalid")
    if not isinstance(finished, datetime) or finished.tzinfo is None or finished.utcoffset().total_seconds() != 0:
        raise ValueError("utc_clock_required")
    if finished < started:
        raise ValueError("clock_moved_backwards")
    record = {
        "schema": "dipsaus_research_source_observation_v1",
        "provider": "Finnhub", "endpoint": "/api/v1/quote", "symbol_requested": symbol,
        "request_started_utc": started.isoformat(),
        "response_finished_utc": finished.isoformat(),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_bytes": len(raw), "raw_response_hex": raw.hex(),
        "source_timestamp_claim_unverified": body.get("t"),
        "external_receipt_verified": False,
        "provider_identity_independently_verified": False,
        "prospective_signal_proven": False,
        "research_only": True, "trade_ready": False,
    }
    # Exclusive create: never overwrite an earlier observation.
    with destination.open("x", encoding="utf-8") as output:
        json.dump(record, output, sort_keys=True, separators=(",", ":"))
        output.write("\n")
    return {"status": "source_observation_locally_captured",
            "source_sha256": record["source_sha256"],
            "research_only": True, "trade_ready": False}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python research_capture_finnhub_observation.py SYMBOL OUTPUT_PATH")
    result = capture(sys.argv[1], sys.argv[2], token=os.environ.get("FINNHUB_API_KEY", ""))
    print(json.dumps(result, sort_keys=True))
