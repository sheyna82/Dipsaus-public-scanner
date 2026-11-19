"""Conservative US market-hours code-freeze advisory gate.

Weekdays 09:25–16:00 America/New_York are frozen, including holidays.
This is a workflow guard, NOT a GitHub branch protection rule.
"""
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")


def code_freeze_active(now=None):
    now = datetime.now(timezone.utc) if now is None else now
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")
    local = now.astimezone(NY)
    return local.weekday() < 5 and time(9, 25) <= local.time() < time(16, 0)


if __name__ == "__main__":
    import os
    frozen = code_freeze_active()
    print("US_CODE_FREEZE=" + ("ACTIVE" if frozen else "INACTIVE"))
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"frozen={'true' if frozen else 'false'}\n")
    # Exit nonzero in enforcement mode, e.g. before workflow write steps.
    if frozen and os.environ.get("DIPSAUS_ENFORCE_CODE_FREEZE") == "1":
        raise SystemExit("US market-hours code freeze active; abort write workflow")
