"""Offline US regular-session timestamp classification; never trade authorization.

Uses zoneinfo America/New_York for DST. Does not assert exchange holidays,
early closes, halts or instrument-specific trading calendars.
"""
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

def classify_regular_session(bars, *, timeframe):
    blocks = []
    if timeframe not in ("daily", "hourly"):
        blocks.append("TIMEFRAME_UNSUPPORTED")
    if not isinstance(bars, list) or not bars:
        blocks.append("BARS_MISSING")
    if blocks:
        return {"status": "UNKNOWN", "blocks": sorted(set(blocks)), "trade_ready": False}
    for bar in bars:
        if not isinstance(bar, dict) or not isinstance(bar.get("time"), str):
            blocks.append("BAR_TIME_MISSING")
            break
        try:
            dt = datetime.fromisoformat(bar["time"].replace("Z", "+00:00"))
        except (ValueError, OverflowError):
            blocks.append("BAR_TIME_INVALID")
            break
        if dt.tzinfo is None or dt.utcoffset() is None:
            blocks.append("BAR_TIME_NOT_AWARE")
            break
        local = dt.astimezone(NY)
        if local.weekday() >= 5:
            blocks.append("WEEKEND_BAR")
        if timeframe == "hourly":
            # Bar timestamps interpreted as start-of-interval, not end.
            if not (time(9, 30) <= local.time() < time(16, 0)):
                blocks.append("OUTSIDE_REGULAR_SESSION")
    # This checks only coarse weekday/clock bounds. Holidays and early
    # closes need an independently verified exchange calendar.
    return {"status": "CLOCK_SCREENED_UNVERIFIED" if not blocks else "UNKNOWN",
            "blocks": sorted(set(blocks)), "exchange_calendar_verified": False,
            "trade_ready": False}
