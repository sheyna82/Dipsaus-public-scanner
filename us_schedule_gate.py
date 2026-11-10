"""Fail-closed US regular-session gate for scheduled and external workflow starts.

This is a scheduling safeguard with a pinned NYSE holiday calendar, not trade authorization.
"""
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")

# Published NYSE cash-equity schedule (2026–2027).
# Source: NYSE Group release, 2025-12-23, 2026-2028 holiday calendar.
# https://ir.theice.com/press/news-details/2025/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/
# Note: July 2 in 2026 and 2027 is NOT an NYSE cash-equities early close.
# Unknown years fail closed pending calendar review. Unscheduled exchange
# closures are not represented here and require an operational override.
CLOSED_DAYS = frozenset(date.fromisoformat(day) for day in (
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
    "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
    "2026-11-26", "2026-12-25",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26",
    "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06",
    "2027-11-25", "2027-12-24",
))
EARLY_CLOSE_DAYS = frozenset(date.fromisoformat(day) for day in (
    "2026-11-27", "2026-12-24", "2027-11-26",
))
SUPPORTED_YEARS = frozenset((2026, 2027))



def scheduled_us_scan_allowed(event_name, now=None):
    if event_name not in ("schedule", "workflow_dispatch"):
        return False
    now = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None:
        return False
    local = now.astimezone(NEW_YORK)
    if local.year not in SUPPORTED_YEARS or local.weekday() >= 5:
        return False
    if local.date() in CLOSED_DAYS:
        return False
    close = time(13, 0) if local.date() in EARLY_CLOSE_DAYS else time(16, 0)
    return time(9, 30) <= local.time() < close


if __name__ == "__main__":
    import os
    allowed = scheduled_us_scan_allowed(os.environ.get("GITHUB_EVENT_NAME", ""))
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        raise SystemExit("GITHUB_OUTPUT is required")
    with open(output, "a", encoding="utf-8") as handle:
        handle.write(f"allowed={'true' if allowed else 'false'}\n")
    print("US_SCHEDULE_GATE: " + ("ALLOW" if allowed else "SKIP_OUTSIDE_REGULAR_SESSION"))
