"""Offline diagnostic of public daily CSV responses, without leaking response bodies.

Distinguishes rate limiting, HTTP failures, HTML challenges, and CSV errors.
"""
import csv
import io
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def diagnose_response(status, content_type, body):
    if status == 429:
        return {"status": "DATA_UNAVAILABLE", "reason": "rate_limited"}
    if status != 200:
        return {"status": "DATA_UNAVAILABLE", "reason": "http_status", "http_status": status}
    if len(body) > 100_000:
        return {"status": "DATA_UNAVAILABLE", "reason": "oversized"}
    if b"<html" in body[:512].lower() or b"<!doctype html" in body[:512].lower():
        return {"status": "DATA_UNAVAILABLE", "reason": "html_response"}
    try:
        reader = csv.DictReader(io.StringIO(body.decode("utf-8-sig")))
        header = tuple(reader.fieldnames or ())
    except (UnicodeError, csv.Error):
        return {"status": "DATA_UNAVAILABLE", "reason": "decode_failure"}
    expected = ("Date", "Open", "High", "Low", "Close", "Volume")
    if header != expected:
        return {"status": "DATA_UNAVAILABLE", "reason": "unexpected_schema",
                "column_count": len(header)}
    return {"status": "CSV_HEADER_OBSERVED", "content_type": content_type.split(";")[0],
            "trade_ready": False}


def diagnose_url(url):
    try:
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 DIPSAUS-offline-research"}),
                     timeout=12) as response:
            return diagnose_response(response.status, response.headers.get("Content-Type", ""),
                                     response.read(100_001))
    except HTTPError as exc:
        return {"status": "DATA_UNAVAILABLE", "reason": "http_status", "http_status": exc.code}
    except (OSError, URLError, TimeoutError) as exc:
        return {"status": "DATA_UNAVAILABLE", "reason": type(exc).__name__}


if __name__ == "__main__":
    import json
    from research_probe_four_event_tickers import BASE, SYMBOLS
    for symbol in SYMBOLS:
        print(json.dumps({"symbol": symbol, **diagnose_url(BASE.format(symbol=symbol))},
                         sort_keys=True))
