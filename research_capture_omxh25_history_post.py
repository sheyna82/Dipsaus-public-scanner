"""Isolated, fail-closed raw capture of the Nasdaq HistoryData POST response.

The request shape comes from the issuer-hosted History.js script. Dates and
time-of-day must be supplied explicitly and reviewed; no implicit guesses.
This is NOT a validation of official EOD field semantics.
"""
import base64
import hashlib
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from research_capture_omxh25_issuer_raw import NoRedirects, MAX_BYTES

ENDPOINT = "https://beta.indexes.nasdaqomx.com/Index/HistoryData"
ISO_LOCAL = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")

def capture_history_post(destination, start_date, end_date, time_of_day, fetch=None):
    if not (ISO_LOCAL.fullmatch(start_date) and ISO_LOCAL.fullmatch(end_date)):
        raise ValueError("UNREVIEWED_DATE_FORMAT")
    if not (start_date < end_date):
        raise ValueError("INVALID_DATE_RANGE")
    if not isinstance(time_of_day, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", time_of_day):
        raise ValueError("UNREVIEWED_TIME_OF_DAY")
    path = Path(destination)
    if path.exists():
        raise FileExistsError("IMMUTABLE_CAPTURE_EXISTS")
    if not path.parent.is_dir():
        raise ValueError("DESTINATION_PARENT_MISSING")
    fields = {"id": "OMXH25", "startDate": start_date,
              "endDate": end_date, "timeOfDay": time_of_day}
    request = urllib.request.Request(ENDPOINT,
        data=urllib.parse.urlencode(fields).encode("ascii"),
        headers={"Accept": "application/json",
                 "Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": "DipsausIssuerResearchCapture/1.0",
                 "Referer": "https://beta.indexes.nasdaqomx.com/Index/History/OMXH25"},
        method="POST")
    opener = fetch or urllib.request.build_opener(NoRedirects()).open
    with opener(request, timeout=20) as response:
        if response.status != 200 or response.geturl() != ENDPOINT:
            raise ValueError("HISTORY_POST_HTTP_OR_REDIRECT_FAILURE")
        raw = response.read(MAX_BYTES + 1)
        content_type = response.headers.get("Content-Type", "")
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("HISTORY_POST_BYTES_INVALID")
    receipt = {
        "schema": "dipsaus_omxh25_history_post_candidate_v1",
        "source_url": ENDPOINT, "http_method": "POST", "request_fields": fields,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": 200, "content_type": content_type,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_raw_base64": base64.b64encode(raw).decode("ascii"),
        "official_eod_raw_bytes_verified": False,
        "benchmark_identity_verified": False,
        "research_only": True, "trade_ready": False,
    }
    with path.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    return {"status": "history_post_raw_captured_unverified",
            "source_sha256": receipt["source_sha256"], "bytes": len(raw),
            "content_type": content_type, "trade_ready": False}

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        raise SystemExit("usage: python research_capture_omxh25_history_post.py OUTPUT START_ISO_LOCAL END_ISO_LOCAL TIME_OF_DAY")
    print(json.dumps(capture_history_post(*sys.argv[1:]), sort_keys=True))
