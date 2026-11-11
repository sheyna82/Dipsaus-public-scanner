"""Fail-closed horizon coverage check for frozen daily OHLCV research inputs."""
from datetime import date
import math


def audit_daily_ohlcv_horizon(rows, *, minimum_sessions=16):
    """Require >15 sessions per symbol before considering 15-session outcomes.

    This is a necessary coverage check, not proof of an executable strategy.
    """
    if not isinstance(minimum_sessions, int) or isinstance(minimum_sessions, bool) or minimum_sessions < 2:
        raise ValueError("INVALID_MINIMUM_SESSIONS")
    if not isinstance(rows, list) or not rows:
        raise ValueError("EMPTY_OHLCV_ROWS")
    groups = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("INVALID_OHLCV_ROW")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("INVALID_OHLCV_SYMBOL")
        try:
            trading_day = date.fromisoformat(row["date"])
        except (KeyError, ValueError, TypeError):
            raise ValueError("INVALID_OHLCV_DATE") from None
        if trading_day.weekday() >= 5:
            raise ValueError("WEEKEND_OHLCV_SESSION")
        values = []
        for key in ("open", "high", "low", "close"):
            v = row.get(key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
                raise ValueError("INVALID_OHLCV_PRICE")
            values.append(v)
        o, h, l, c = values
        if not l <= min(o, c) <= max(o, c) <= h:
            raise ValueError("INVALID_OHLCV_RANGE")
        key = symbol.strip().upper()
        groups.setdefault(key, set())
        if trading_day in groups[key]:
            raise ValueError("DUPLICATE_OHLCV_SESSION")
        groups[key].add(trading_day)
    coverage = {symbol: {"sessions": len(dates),
                         "fifteen_session_outcomes_possible": len(dates) >= minimum_sessions}
                for symbol, dates in sorted(groups.items())}
    return {"status": "RESEARCH_ONLY_HORIZON_COVERAGE",
            "minimum_sessions_assumption": minimum_sessions,
            "symbols": coverage,
            "all_symbols_eligible": all(v["fifteen_session_outcomes_possible"] for v in coverage.values()),
            "weekend_sessions_rejected": True,
            "calendar_continuity_verified": False,
            "source_independently_verified": False,
            "trade_ready": False}
