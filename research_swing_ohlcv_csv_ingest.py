"""Offline reproducible CSV price-data ingestion for swing research.

Reads a local UTF-8 CSV with session_date,open,high,low,close,volume.
Does not download data or imply a data license. Records file SHA-256 and
validates bars before they may be used in an experiment.
"""
import csv
import hashlib
from pathlib import Path
from research_swing_ohlcv_data_audit import validate_daily_ohlcv_bars

COLUMNS = ("session_date", "open", "high", "low", "close", "volume")


def load_verified_ohlcv_csv(path, *, min_sessions=15):
    path = Path(path)
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    import io
    reader = csv.DictReader(io.StringIO(text), strict=True)
    if reader.fieldnames != list(COLUMNS):
        raise ValueError("unexpected_ohlcv_columns")
    bars = []
    for row in reader:
        if None in row or set(row) != set(COLUMNS):
            raise ValueError("malformed_ohlcv_row")
        bars.append(dict(row))
    audit = validate_daily_ohlcv_bars(bars, min_sessions=min_sessions)
    return {
        "research_only": True, "trade_ready": False,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bar_count": len(bars),
        "audit": audit,
        "bars": bars,
        "provider_identity_verified": False,
        "licensing_verified": False,
    }
