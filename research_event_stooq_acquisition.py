"""Explicit, opt-in historical CSV acquisition for offline event research.

Not used by live scanner or CI. Download is restricted to Stooq's public
daily CSV endpoint; prices are unadjusted/vendor-dependent and must be
independently checked before interpreting returns. Never fetch future data.
"""
import csv
import hashlib
import io
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

ALLOWED_HOST = "stooq.com"
SYMBOLS = {"TSLA", "META", "COHU", "AMZN", "PLTR", "AMD", "SPY"}
MAX_BYTES = 2_000_000


def parse_stooq_csv(payload):
    if not isinstance(payload, bytes) or not payload or len(payload) > MAX_BYTES:
        raise ValueError("invalid_csv_payload_size")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid_csv_encoding") from exc
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != ["Date", "Open", "High", "Low", "Close", "Volume"]:
        raise ValueError("unexpected_csv_columns")
    rows = []
    previous = None
    from decimal import Decimal, InvalidOperation
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("malformed_csv_row")
        try:
            session = date.fromisoformat(row["Date"])
            close = Decimal(row["Close"])
            volume = Decimal(row["Volume"])
        except (ValueError, InvalidOperation, TypeError) as exc:
            raise ValueError("invalid_csv_observation") from exc
        if previous is not None and session <= previous:
            raise ValueError("csv_dates_not_strictly_increasing")
        if not close.is_finite() or close <= 0 or not volume.is_finite() or volume < 0:
            raise ValueError("invalid_csv_observation")
        rows.append({"date": session.isoformat(), "close": str(close),
                     "volume": str(volume)})
        previous = session
    if not rows:
        raise ValueError("empty_csv_history")
    return rows


def acquire_stooq_history(symbol, start, end, output_dir, *, allow_network=False):
    """Manual-only fetch; output is unverified vendor evidence, never a signal."""
    if not allow_network:
        raise ValueError("explicit_network_opt_in_required")
    if symbol not in SYMBOLS:
        raise ValueError("symbol_not_allowlisted")
    start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    if start_date > end_date or end_date > date.today():
        raise ValueError("invalid_or_future_date_range")
    query = urlencode({"s": symbol.lower() + ".us", "d1": start_date.strftime("%Y%m%d"),
                       "d2": end_date.strftime("%Y%m%d"), "i": "d"})
    url = "https://stooq.com/q/d/l/?" + query
    if urlparse(url).hostname != ALLOWED_HOST:
        raise ValueError("source_host_not_allowed")
    with urlopen(url, timeout=15) as response:
        if urlparse(response.geturl()).hostname != ALLOWED_HOST:
            raise ValueError("unexpected_redirect_host")
        payload = response.read(MAX_BYTES + 1)
    rows = parse_stooq_csv(payload)
    if any(not start <= row["date"] <= end for row in rows):
        raise ValueError("csv_date_outside_requested_range")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    filename = f"{symbol}_{start}_{end}"
    (root / (filename + ".csv")).write_bytes(payload)
    metadata = {"symbol": symbol, "requested_start": start, "requested_end": end,
                "source_url": url, "content_sha256": hashlib.sha256(payload).hexdigest(),
                "row_count": len(rows), "source_authenticity_verified": False,
                "exchange_calendar_verified": False, "trade_ready": False}
    (root / (filename + ".json")).write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata
