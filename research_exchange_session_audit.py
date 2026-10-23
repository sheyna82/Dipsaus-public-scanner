"""Validate price dates against a caller-supplied exchange session schedule.

No calendar dependency or network access. The caller must provide sessions
from a pinned, independently reviewed calendar release.
"""
from datetime import date


def audit_expected_sessions(price_dates, expected_sessions):
    def parse(values, name):
        if not isinstance(values, (list, tuple)) or not values:
            raise ValueError("invalid_" + name)
        result = []
        for value in values:
            if not isinstance(value, str):
                raise ValueError("invalid_" + name)
            try:
                parsed = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("invalid_" + name) from exc
            if parsed.isoformat() != value:
                raise ValueError("invalid_" + name)
            result.append(parsed)
        if any(b <= a for a, b in zip(result, result[1:])):
            raise ValueError("unordered_" + name)
        return result

    prices = parse(price_dates, "price_dates")
    sessions = parse(expected_sessions, "expected_sessions")
    if prices[0] < sessions[0] or prices[-1] > sessions[-1]:
        raise ValueError("calendar_range_does_not_cover_prices")
    actual = set(prices)
    scheduled = set(sessions)
    missing = [d.isoformat() for d in sessions
               if prices[0] <= d <= prices[-1] and d not in actual]
    unexpected = [d.isoformat() for d in prices if d not in scheduled]
    return {"missing_expected_sessions": missing,
            "unexpected_price_dates": unexpected,
            "price_rows": len(prices),
            "calendar_sessions_in_range": sum(prices[0] <= d <= prices[-1]
                                              for d in sessions),
            "complete_against_supplied_calendar": not missing and not unexpected,
            "calendar_provenance_verified": False,
            "trade_ready": False}
