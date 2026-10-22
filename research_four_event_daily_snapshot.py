"""Offline research: classify completed daily event sessions for four tickers.

This is a descriptive current snapshot, not a historical earnings backtest.
Only uses the Yahoo data probe; no persistence or notifications.
"""
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from research_probe_alternative_daily_source import BASE, SYMBOLS
from research_audit_four_event_ohlcv import audit_chart
from dipsaus_offline_ohlcv_features import _valid
from dipsaus_offline_event_daily_evidence import derive_daily_event_evidence
import csv
import tempfile
from pathlib import Path


def snapshot(symbol, payload):
    quality = audit_chart(payload, symbol)
    if quality["status"] != "OHLCV_VALIDATED":
        return quality
    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    # Convert UTC date for daily bars; exchange-local date must be verified
    # separately before using for trading.
    rows = []
    for i, ts in enumerate(timestamps):
        rows.append({"date": datetime.fromtimestamp(ts, timezone.utc).date().isoformat(),
                     **{key: quote[key][i] for key in ("open", "high", "low", "close", "volume")}})
    if not _valid(rows):
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "invalid_session_dates"}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "history.csv"
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(("Date", "Open", "High", "Low", "Close", "Volume"))
            for row in rows:
                writer.writerow(tuple(row[k] for k in ("date", "open", "high", "low", "close", "volume")))
        evidence = derive_daily_event_evidence(str(path),
                   expected_session=rows[-1]["date"], source_verified=True)
    return {"symbol": symbol, "status": "DESCRIPTIVE_SNAPSHOT",
            "session_utc": rows[-1]["date"],
            "trend_confirmed": evidence.get("trend_confirmed"),
            "downside_warning": evidence.get("downside_warning"),
            "event_verified": False, "earnings_timing_verified": False,
            "historical_outcome_tested": False, "trade_ready": False}


def fetch_snapshot(symbol):
    try:
        with urlopen(Request(BASE.format(symbol=symbol),
                             headers={"User-Agent": "Mozilla/5.0"}), timeout=12) as response:
            raw = response.read(300_001)
        if len(raw) > 300_000:
            return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "oversized"}
        return snapshot(symbol, json.loads(raw))
    except (OSError, ValueError, TimeoutError, UnicodeError):
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "fetch_failed"}


if __name__ == "__main__":
    for symbol in SYMBOLS:
        print(json.dumps(fetch_snapshot(symbol), sort_keys=True))
