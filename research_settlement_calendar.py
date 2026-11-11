"""Research-only settlement calendars; holidays require explicit supplied dates."""
from datetime import date, timedelta


def settlement_business_date(exit_date, *, lag_business_days, holidays=()):
    """Weekend-aware settlement, with explicitly supplied holiday calendar.

    No exchange, currency or broker calendar is inferred. Missing holidays can
    make the result earlier than real settlement; not suitable for execution.
    """
    if not isinstance(exit_date, date) or isinstance(exit_date, __import__("datetime").datetime):
        raise ValueError("INVALID_EXIT_DATE")
    if (not isinstance(lag_business_days, int) or isinstance(lag_business_days, bool)
            or lag_business_days < 0):
        raise ValueError("INVALID_BUSINESS_DAY_LAG")
    if not isinstance(holidays, (list, tuple, set, frozenset)):
        raise ValueError("INVALID_HOLIDAY_CALENDAR")
    if any(not isinstance(day, date) or isinstance(day, __import__("datetime").datetime)
           for day in holidays):
        raise ValueError("INVALID_HOLIDAY_CALENDAR")
    blocked = set(holidays)
    if exit_date.weekday() >= 5 or exit_date in blocked:
        raise ValueError("EXIT_NOT_BUSINESS_DAY")
    current = exit_date
    remaining = lag_business_days
    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in blocked:
            remaining -= 1
    return {
        "settlement_date": current.isoformat(),
        "business_day_lag": lag_business_days,
        "holiday_calendar_explicit": True,
        "holiday_calendar_coverage_verified": False,
        "broker_rule_verified": False,
        "trade_ready": False,
        "automatic_orders": False,
    }
