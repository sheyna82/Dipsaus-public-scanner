"""Strict offline CSV price-bar structural audit, not a provenance certificate."""
import csv
import io
import math
from datetime import date

REQUIRED = ("date", "open", "high", "low", "close", "volume")


def audit_daily_price_csv(payload):
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("invalid_payload")
    try:
        content = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid_utf8") from exc
    reader = csv.DictReader(io.StringIO(content, newline=""))
    if reader.fieldnames is None or tuple(reader.fieldnames) != REQUIRED:
        raise ValueError("invalid_columns")
    previous = None
    count = 0
    for row in reader:
        if None in row or any(row.get(key) is None for key in REQUIRED):
            raise ValueError("malformed_row")
        try:
            day = date.fromisoformat(row["date"])
            values = [float(row[key]) for key in REQUIRED[1:]]
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid_price_row") from exc
        if previous is not None and day <= previous:
            raise ValueError("unordered_or_duplicate_dates")
        previous = day
        opening, high, low, close, volume = values
        if (not all(math.isfinite(value) for value in values)
                or min(opening, high, low, close) <= 0 or volume < 0
                or high < max(opening, close, low)
                or low > min(opening, close, high)):
            raise ValueError("invalid_ohlcv")
        count += 1
    if not count:
        raise ValueError("empty_prices")
    return {
        "accepted": True,
        "rows": count,
        "first_date": None,  # No source timestamp guarantees are inferred.
        "provenance_verified": False,
        "adjustments_verified": False,
        "point_in_time_verified": False,
        "trade_ready": False,
    }
