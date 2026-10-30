"""Read-only research audit of Yahoo daily chart bars for four event tickers.

No persistent data, secrets, orders, notifications, or live pipeline changes.
"""
import json
import math
from datetime import datetime, timezone
from research_probe_alternative_daily_source import SYMBOLS, BASE
from urllib.request import Request, urlopen


def audit_chart(payload, symbol):
    try:
        result = payload["chart"]["result"][0]
        if result["meta"].get("symbol", "").upper() != symbol:
            return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "symbol_mismatch"}
        ts = result["timestamp"]
        q = result["indicators"]["quote"][0]
        fields = ("open", "high", "low", "close", "volume")
        if len(ts) < 22 or any(len(q[k]) != len(ts) for k in fields):
            return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "incomplete_history"}
        if any(type(t) is not int for t in ts) or any(a >= b for a, b in zip(ts, ts[1:])):
            return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "nonmonotonic_timestamps"}
        for i in range(len(ts)):
            o, h, l, c, v = (q[k][i] for k in fields)
            if any(type(x) not in (int, float) or not math.isfinite(x)
                   for x in (o, h, l, c, v)):
                return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "missing_or_nonfinite"}
            if min(o, h, l, c) <= 0 or v <= 0 or not l <= min(o, c) <= max(o, c) <= h:
                return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "invalid_ohlcv"}
        return {"symbol": symbol, "status": "OHLCV_VALIDATED",
                "bars": len(ts),
                "first_session_utc": datetime.fromtimestamp(ts[0], timezone.utc).date().isoformat(),
                "last_session_utc": datetime.fromtimestamp(ts[-1], timezone.utc).date().isoformat(),
                "corporate_actions_verified": False,
                "exchange_session_calendar_verified": False,
                "historical_forecast_tested": False,
                "trade_ready": False}
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "invalid_payload"}


def audit_symbol(symbol):
    try:
        with urlopen(Request(BASE.format(symbol=symbol),
                             headers={"User-Agent": "Mozilla/5.0"}), timeout=12) as response:
            payload = response.read(300_001)
        if len(payload) > 300_000:
            return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "oversized"}
        return audit_chart(json.loads(payload), symbol)
    except (OSError, ValueError, TimeoutError, UnicodeError):
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "fetch_failed"}


if __name__ == "__main__":
    for symbol in SYMBOLS:
        print(json.dumps(audit_symbol(symbol), sort_keys=True))
