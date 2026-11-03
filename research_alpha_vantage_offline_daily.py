"""Validate offline Alpha Vantage daily JSON without fetching or trading.

Input bytes are untrusted and do not independently establish provenance,
freshness, or prospective registration.
"""
import json
import math
from datetime import date


def inspect_alpha_vantage_daily_bytes(source_bytes, *, expected_symbol, as_of_session):
    if not isinstance(source_bytes, bytes) or not source_bytes or len(source_bytes) > 5_000_000:
        raise ValueError("invalid_source_bytes")
    if not isinstance(expected_symbol, str) or not expected_symbol or not expected_symbol.isascii():
        raise ValueError("invalid_expected_symbol")
    try:
        session = date.fromisoformat(as_of_session)
        data = json.loads(source_bytes)
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise ValueError("invalid_daily_payload") from exc
    if not isinstance(data, dict):
        raise ValueError("invalid_daily_payload")
    if any(k in data for k in ("Error Message", "Note", "Information")):
        raise ValueError("provider_error_or_rate_limit")
    metadata = data.get("Meta Data")
    series = data.get("Time Series (Daily)")
    if not isinstance(metadata, dict) or not isinstance(series, dict):
        raise ValueError("missing_daily_series")
    if metadata.get("2. Symbol") != expected_symbol:
        raise ValueError("provider_symbol_mismatch")
    if not series or len(series) > 10000:
        raise ValueError("invalid_daily_series")
    parsed = {}
    for day, row in series.items():
        try:
            d = date.fromisoformat(day)
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid_bar_date") from exc
        if d.isoformat() != day or d > session:
            raise ValueError("future_or_invalid_bar")
        if not isinstance(row, dict):
            raise ValueError("invalid_daily_bar")
        values = []
        for field in ("1. open", "2. high", "3. low", "4. close", "5. volume"):
            raw = row.get(field)
            if not isinstance(raw, str):
                raise ValueError("invalid_daily_bar")
            try:
                value = float(raw)
            except ValueError as exc:
                raise ValueError("invalid_daily_bar") from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError("invalid_daily_bar")
            values.append(value)
        op, hi, lo, close, vol = values
        if min(op, hi, lo, close) <= 0 or lo > min(op, close) or hi < max(op, close) or hi < lo or not vol.is_integer():
            raise ValueError("inconsistent_daily_bar")
        parsed[day] = {"open": op, "high": hi, "low": lo, "close": close, "volume": int(vol)}
    if as_of_session not in parsed:
        raise ValueError("requested_session_not_present")
    return {
        "symbol": expected_symbol, "session": as_of_session,
        "bar": parsed[as_of_session], "available_sessions": len(parsed),
        "provider_response_schema_valid": True,
        "provider_authenticity_verified": False,
        "independent_timestamp_proof": False,
        "trade_ready": False, "research_only": True,
    }
