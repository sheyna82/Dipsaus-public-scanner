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



def parse_alpha_vantage_daily(payload):
    """Alpha Vantage TIME_SERIES_DAILY raw close; quota notices fail closed."""
    if not isinstance(payload, dict):
        raise ValueError("vendor_error")
    series = payload.get("Time Series (Daily)")
    if not isinstance(series, dict) or not series:
        raise ValueError("vendor_error")
    records = []
    for session, prices in series.items():
        if not isinstance(prices, dict):
            raise ValueError("invalid_daily_record")
        records.append({"date": session, "close": prices.get("4. close")})
    return _normalize(records, "date", "close")



def parse_finnhub_candles(payload):
    """Finnhub stock/candle response: t Unix seconds, c close, s status.

    Historical availability and free-tier entitlement must be verified.
    """
    from datetime import datetime, timezone
    if not isinstance(payload, dict) or payload.get("s") != "ok":
        raise ValueError("vendor_error")
    timestamps, closes = payload.get("t"), payload.get("c")
    if not isinstance(timestamps, list) or not isinstance(closes, list):
        raise ValueError("invalid_candle_arrays")
    if not timestamps or len(timestamps) != len(closes):
        raise ValueError("invalid_candle_arrays")
    records = []
    for stamp, close in zip(timestamps, closes):
        if isinstance(stamp, bool) or not isinstance(stamp, int):
            raise ValueError("invalid_candle_timestamp")
        try:
            session = datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat()
        except (OverflowError, ValueError, OSError) as exc:
            raise ValueError("invalid_candle_timestamp") from exc
        records.append({"date": session, "close": close})
    return _normalize(records, "date", "close")



def parse_massive_daily_aggregates(payload, *, adjusted):
    """Massive daily aggregates; enforce requested split-adjustment mode.

    Timestamps are Unix milliseconds. This adapter does not fetch or authenticate.
    """
    from datetime import datetime, timezone
    if not isinstance(adjusted, bool):
        raise ValueError("adjustment_mode_required")
    if not isinstance(payload, dict) or payload.get("status") != "OK":
        raise ValueError("vendor_error")
    # The API request controls adjustment; responses need not echo that flag.
    # Reject an explicit contradictory field, but never infer verification from its absence.
    if "adjusted" in payload and payload["adjusted"] is not adjusted:
        raise ValueError("adjustment_mode_mismatch")
    bars = payload.get("results")
    if not isinstance(bars, list) or not bars:
        raise ValueError("missing_daily_prices")
    records = []
    for bar in bars:
        if not isinstance(bar, dict):
            raise ValueError("invalid_daily_record")
        stamp = bar.get("t")
        if isinstance(stamp, bool) or not isinstance(stamp, int):
            raise ValueError("invalid_candle_timestamp")
        try:
            session = datetime.fromtimestamp(stamp / 1000, tz=timezone.utc).date().isoformat()
        except (ValueError, OverflowError, OSError) as exc:
            raise ValueError("invalid_candle_timestamp") from exc
        records.append({"date": session, "close": bar.get("c")})
    return _normalize(records, "date", "close")
