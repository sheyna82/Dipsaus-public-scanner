"""Strict local daily OHLCV CSV reader for exploratory research.

Supports Stooq-style Date,Open,High,Low,Close,Volume. No network,
provider endorsement, provenance fabrication or live signals.
"""
import csv
from pathlib import Path
from dipsaus_offline_ohlcv_features import _valid

MAX_CSV_BYTES = 10_000_000
MAX_BARS = 15000
COLUMNS = ("Date", "Open", "High", "Low", "Close", "Volume")


def load_local_ohlcv_csv(path):
    try:
        source = Path(path)
        if not source.is_file() or source.stat().st_size > MAX_CSV_BYTES:
            return None
        bars = []
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or tuple(reader.fieldnames) != COLUMNS:
                return None
            for row in reader:
                if len(bars) >= MAX_BARS or None in row or any(v is None for v in row.values()):
                    return None
                bars.append({"date": row["Date"],
                             "open": float(row["Open"]), "high": float(row["High"]),
                             "low": float(row["Low"]), "close": float(row["Close"]),
                             "volume": float(row["Volume"])})
        return bars if _valid(bars) else None
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError):
        return None
