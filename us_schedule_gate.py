"""Fail-closed US regular-session gate for scheduled and external workflow starts.

This is a scheduling safeguard, not an exchange holiday calendar or trade authorization.
"""
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")


def scheduled_us_scan_allowed(event_name, now=None):
    if event_name not in ("schedule", "workflow_dispatch"):
        return False
    now = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None:
        return False
    local = now.astimezone(NEW_YORK)
    return local.weekday() < 5 and time(9, 30) <= local.time() < time(16, 0)


if __name__ == "__main__":
    import os
    allowed = scheduled_us_scan_allowed(os.environ.get("GITHUB_EVENT_NAME", ""))
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        raise SystemExit("GITHUB_OUTPUT is required")
    with open(output, "a", encoding="utf-8") as handle:
        handle.write(f"allowed={'true' if allowed else 'false'}\n")
    print("US_SCHEDULE_GATE: " + ("ALLOW" if allowed else "SKIP_OUTSIDE_REGULAR_SESSION"))
