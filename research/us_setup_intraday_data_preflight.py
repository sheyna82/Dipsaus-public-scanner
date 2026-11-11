"""Fail-closed preflight for intraday US setup historical bar inputs.

This adapter does not fetch data or certify historical labels. Daily OHLC
data must never be silently treated as minute bars for intraday confirmation.
"""
from datetime import datetime, timezone
import math


def audit_intraday_bars(rows, *, max_gap_minutes=120, min_bars=20):
    if not isinstance(rows, list) or len(rows) < min_bars:
        return {"usable": False, "reason": "INSUFFICIENT_BARS", "bar_count": len(rows) if isinstance(rows, list) else 0}
    previous = None
    gaps = []
    normalized = []
    for row in rows:
        if not isinstance(row, dict) or "timestamp" not in row:
            return {"usable": False, "reason": "MISSING_INTRADAY_TIMESTAMP"}
        try:
            ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            lo, close = float(row["low"]), float(row["close"])
        except (ValueError, TypeError, KeyError, AttributeError):
            return {"usable": False, "reason": "INVALID_BAR"}
        if ts.tzinfo is None or not math.isfinite(lo) or not math.isfinite(close) or lo <= 0 or close < lo:
            return {"usable": False, "reason": "INVALID_BAR"}
        utc = ts.astimezone(timezone.utc)
        if previous is not None:
            gap = (utc - previous).total_seconds() / 60
            if gap <= 0:
                return {"usable": False, "reason": "NON_MONOTONIC_BARS"}
            gaps.append(gap)
        previous = utc
        normalized.append({"timestamp": utc.isoformat(), "low": lo, "close": close})
    # Overnight/weekend gaps are expected. Require a minimum of observed
    # consecutive intraday bars, not merely an intraday-looking timestamp.
    intraday_steps = sum(0 < gap <= max_gap_minutes for gap in gaps)
    if intraday_steps < min_bars - 2:
        return {"usable": False, "reason": "NOT_CONTIGUOUS_INTRADAY", "bar_count": len(rows),
                "intraday_steps": intraday_steps}
    return {"usable": True, "reason": None, "bar_count": len(rows),
            "intraday_steps": intraday_steps, "bars": normalized,
            "provider_verified": False, "session_calendar_verified": False,
            "corporate_actions_verified": False, "research_only": True}
