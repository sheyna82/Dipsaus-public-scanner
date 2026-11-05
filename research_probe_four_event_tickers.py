"""Research-only no-key OHLCV provider availability probe for four US tickers.

Fetches a small bounded response, reports availability/schema, never scores trades.
Network failures are explicit DATA_UNAVAILABLE. No files, tokens or alerts.
"""
import csv
import io
import json
from urllib.request import Request, urlopen

SYMBOLS = ("amzn.us", "cohu.us", "meta.us", "tsla.us")
BASE = "https://stooq.com/q/d/l/?s={symbol}&i=d&d1=20260901&d2=20261021"
REQUIRED = ("Date", "Open", "High", "Low", "Close", "Volume")


def probe_symbol(symbol, fetch=None):
    if symbol not in SYMBOLS:
        return {"symbol": symbol, "status": "REJECTED", "reason": "not_allowlisted"}
    url = BASE.format(symbol=symbol)
    try:
        if fetch is None:
            request = Request(url, headers={"User-Agent": "DIPSAUS-offline-research/1.0"})
            with urlopen(request, timeout=12) as response:
                data = response.read(100_001)
        else:
            data = fetch(url)
        if len(data) > 100_000:
            return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "reason": "oversized"}
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
        if tuple(reader.fieldnames or ()) != REQUIRED:
            return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "reason": "unexpected_schema"}
        rows = list(reader)
        if len(rows) < 22 or any(not all(r.get(k) for k in REQUIRED) for r in rows):
            return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "reason": "insufficient_rows"}
        return {"symbol": symbol, "status": "SCHEMA_OBSERVED",
                "rows": len(rows), "first_date": rows[0]["Date"],
                "last_date": rows[-1]["Date"],
                "adjustment_policy_verified": False,
                "provider_rights_verified": False,
                "trade_ready": False}
    except (OSError, UnicodeError, ValueError, TimeoutError) as exc:
        return {"symbol": symbol, "status": "DATA_UNAVAILABLE",
                "reason": type(exc).__name__}


if __name__ == "__main__":
    for ticker in SYMBOLS:
        print(json.dumps(probe_symbol(ticker), sort_keys=True))
