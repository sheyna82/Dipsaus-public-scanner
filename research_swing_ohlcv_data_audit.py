"""Offline audit of real OHLCV input before a historical swing experiment.

Accept only independently supplied dated daily bars, never manufacture data.
Fail closed on missing dates, duplicate sessions, nonfinite prices, invalid
OHLC relationships or zero volume. Exchange calendars, adjustments, licensing
and provider authenticity require separate checks.
"""
from datetime import date
from decimal import Decimal, InvalidOperation


def _decimal(value):
    if isinstance(value, bool):
        raise ValueError("invalid_market_number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_market_number") from None
    if not number.is_finite():
        raise ValueError("invalid_market_number")
    return number


def validate_daily_ohlcv_bars(bars, *, min_sessions=15):
    if isinstance(min_sessions, bool) or not isinstance(min_sessions, int) or min_sessions < 1:
        raise ValueError("invalid_min_sessions")
    if not isinstance(bars, (list, tuple)) or len(bars) < min_sessions:
        raise ValueError("insufficient_market_history")
    previous = None
    for bar in bars:
        if not isinstance(bar, dict):
            raise ValueError("invalid_bar")
        day = bar.get("session_date")
        if not isinstance(day, str):
            raise ValueError("invalid_session_date")
        try:
            parsed = date.fromisoformat(day)
        except ValueError:
            raise ValueError("invalid_session_date") from None
        if parsed.isoformat() != day or (previous is not None and parsed <= previous):
            raise ValueError("duplicate_or_unsorted_session")
        previous = parsed
        opening, high, low, closing = (_decimal(bar.get(k)) for k in
                                        ("open", "high", "low", "close"))
        volume = _decimal(bar.get("volume"))
        if low <= 0 or opening <= 0 or closing <= 0 or high <= 0:
            raise ValueError("invalid_price")
        if not low <= min(opening, closing) <= max(opening, closing) <= high:
            raise ValueError("inconsistent_ohlc")
        if volume <= 0 or volume != volume.to_integral_value():
            raise ValueError("invalid_volume")
    return {
        "research_only": True, "trade_ready": False,
        "validated_sessions": len(bars),
        "first_session": bars[0]["session_date"],
        "last_session": bars[-1]["session_date"],
        "source_authenticity_verified": False,
        "corporate_actions_verified": False,
        "exchange_calendar_verified": False,
        "data_license_verified": False,
    }
