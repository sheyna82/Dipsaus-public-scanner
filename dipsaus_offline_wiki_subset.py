"""Research-only strict conversion of WIKI/PRICES-style CSV into local OHLCV.

No API calls, no keys, no downloading, no public data redistribution.
Adjusted OHLC must be complete: never mix adjusted and raw columns.
"""
import csv
import math
from datetime import date as calendar_date
from pathlib import Path

from dipsaus_offline_ohlcv_csv import load_local_ohlcv_csv
from dipsaus_offline_history_quality import audit_price_history

MAX_INPUT_BYTES = 10_000_000
RAW = ("open", "high", "low", "close", "volume")
ADJUSTED = ("adj_open", "adj_high", "adj_low", "adj_close", "adj_volume")


def convert_wiki_subset(input_path, output_path, *, symbol, adjusted=True):
    """Convert a prefiltered single-symbol CSV; reject ambiguous provenance."""
    source, target = Path(input_path), Path(output_path)
    if not symbol or not isinstance(symbol, str) or not symbol.isascii() or not all(
            ch.isalnum() or ch in ".-" for ch in symbol) or len(symbol) > 16:
        raise ValueError("invalid_symbol")
    if source.resolve() == target.resolve():
        raise ValueError("output_overwrites_source")
    if not source.is_file() or source.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("invalid_source")
    columns = ADJUSTED if adjusted else RAW
    parsed = []
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"ticker", "date", *columns}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("missing_columns")
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("malformed_row")
            if row["ticker"] != symbol:
                raise ValueError("mixed_symbols")
            values = [float(row[k]) for k in columns]
            if not all(math.isfinite(v) for v in values):
                raise ValueError("nonfinite_value")
            op, hi, lo, cl, vol = values
            if min(op, hi, lo, cl) <= 0 or vol < 0 or hi < max(op, cl, lo) or lo > min(op, cl, hi):
                raise ValueError("invalid_ohlcv")
            try:
                observed_date = calendar_date.fromisoformat(row["date"])
            except ValueError as exc:
                raise ValueError("invalid_date") from exc
            if observed_date.isoformat() != row["date"] or observed_date.weekday() >= 5:
                raise ValueError("invalid_trading_date")
            parsed.append((row["date"], values))
            if len(parsed) > 15000:
                raise ValueError("too_many_bars")
    if len(parsed) < 32 or any(parsed[i][0] >= parsed[i+1][0]
                               for i in range(len(parsed)-1)):
        raise ValueError("invalid_date_order_or_coverage")
    quality = audit_price_history([
        {"date": day, "close": values[3]} for day, values in parsed
    ])
    if quality["findings"]:
        raise ValueError("history_quality_review_required")
    # Validate without writing or replacing the destination on failure.
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                     dir=target.parent, delete=False) as tmp:
        temp_name = tmp.name
        writer = csv.writer(tmp)
        writer.writerow(("Date", "Open", "High", "Low", "Close", "Volume"))
        for date, values in parsed:
            writer.writerow((date, *values))
    try:
        if load_local_ohlcv_csv(temp_name) is None:
            raise ValueError("invalid_converted_history")
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return {"status": "LOCAL_RESEARCH_ONLY", "symbol": symbol,
            "bars": len(parsed), "adjusted": adjusted,
            "provider_adjustment_verified": False,
            "benchmark_compatible_verified": False, "trade_ready": False}
