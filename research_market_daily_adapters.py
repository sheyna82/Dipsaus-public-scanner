"""Offline normalized daily-price adapters; no HTTP requests or credentials.

Only vendor response parsing. Real access and license rights remain unverified.
"""
from datetime import date
from decimal import Decimal, InvalidOperation


def _price(value):
    try:
        result = Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise ValueError("invalid_close") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError("invalid_close")
    return str(result)


def _normalize(records, date_key, close_key):
    if not isinstance(records, list) or not records:
        raise ValueError("missing_daily_prices")
    output = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("invalid_daily_record")
        try:
            session = str(date.fromisoformat(str(record[date_key])[:10]))
            close = _price(record[close_key])
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid_daily_record") from exc
        output.append({"date": session, "close": close})
    output.sort(key=lambda item: item["date"])
    if len({item["date"] for item in output}) != len(output):
        raise ValueError("duplicate_daily_session")
    return output


def parse_tiingo_daily(payload, *, adjusted=False):
    """Tiingo EOD list; caller must choose raw vs dividend/split adjusted."""
    return _normalize(payload, "date", "adjClose" if adjusted else "close")


def parse_twelve_data_daily(payload):
    """Twelve Data time_series JSON; errors fail closed."""
    if not isinstance(payload, dict) or payload.get("status") == "error":
        raise ValueError("vendor_error")
    return _normalize(payload.get("values"), "datetime", "close")
