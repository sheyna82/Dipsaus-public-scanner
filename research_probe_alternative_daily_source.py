"""Research-only alternative public daily source probe (Yahoo chart endpoint).

Reports structural availability only, never treats an HTTP 200 as verified
prices, never emits trade signals. Endpoint may be restricted or change.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SYMBOLS = ("AMZN", "COHU", "META", "TSLA")
BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=3mo&interval=1d"


def probe(symbol, fetch=None):
    if symbol not in SYMBOLS:
        return {"symbol": symbol, "status": "REJECTED"}
    try:
        if fetch is None:
            request = Request(BASE.format(symbol=symbol),
                              headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=12) as response:
                payload = response.read(300_001)
        else:
            payload = fetch(BASE.format(symbol=symbol))
        if len(payload) > 300_000:
            return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "reason": "oversized"}
        data = json.loads(payload)
        chart = data.get("chart", {})
        results = chart.get("result")
        if not isinstance(results, list) or len(results) != 1:
            return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "reason": "missing_result"}
        result = results[0]
        timestamps = result.get("timestamp", [])
        indicators = result.get("indicators", {}).get("quote", [])
        if not isinstance(timestamps, list) or len(timestamps) < 22 or not indicators:
            return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "reason": "insufficient_history"}
        q = indicators[0]
        if any(not isinstance(q.get(field), list) or len(q[field]) != len(timestamps)
               for field in ("open", "high", "low", "close", "volume")):
            return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "reason": "incomplete_ohlcv"}
        return {"symbol": symbol, "status": "STRUCTURE_OBSERVED",
                "bars": len(timestamps), "provider_adjustment_verified": False,
                "calendar_verified": False, "trade_ready": False}
    except HTTPError as exc:
        return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "reason": "http_error",
                "http_status": exc.code}
    except (OSError, URLError, TimeoutError, UnicodeError, ValueError, TypeError, AttributeError):
        return {"symbol": symbol, "status": "DATA_UNAVAILABLE", "reason": "request_or_schema_failure"}


if __name__ == "__main__":
    for symbol in SYMBOLS:
        print(json.dumps(probe(symbol), sort_keys=True))
