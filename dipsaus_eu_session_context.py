"""Conservative European cash-market session context for diagnostics only.

No holidays or exchange-specific calendars are verified here. Never use this
classification to authorize trades or bypass stale quote/report gates.
"""
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

def eu_session_context(now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return "UNKNOWN"
    local = now.astimezone(ZoneInfo("Europe/Amsterdam"))
    if local.weekday() >= 5:
        return "WEEKEND_CLOSED"
    clock = local.time()
    if clock < time(9, 0) or clock >= time(17, 30):
        return "OUTSIDE_CORE_HOURS"
    return "CORE_HOURS_UNVERIFIED_HOLIDAYS"
