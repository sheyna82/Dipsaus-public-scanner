"""Fail-closed core-hours gate for scheduled European workflow runs.

This is a scheduling safeguard, not an exchange holiday calendar or trade
authorization. Manual dispatch remains available for controlled diagnostics.
"""
from datetime import datetime, timezone
from dipsaus_eu_session_context import eu_session_context


def scheduled_eu_scan_allowed(event_name, now=None):
    if event_name == "workflow_dispatch":
        return True
    if event_name != "schedule":
        return False
    now = now if now is not None else datetime.now(timezone.utc)
    return eu_session_context(now) == "CORE_HOURS_UNVERIFIED_HOLIDAYS"


if __name__ == "__main__":
    import os
    allowed = scheduled_eu_scan_allowed(os.environ.get("GITHUB_EVENT_NAME", ""))
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        raise SystemExit("GITHUB_OUTPUT is required")
    with open(output, "a", encoding="utf-8") as handle:
        handle.write(f"allowed={'true' if allowed else 'false'}\n")
    print("EU_SCHEDULE_GATE: " + ("ALLOW" if allowed else "SKIP_OUTSIDE_CORE_OR_UNKNOWN"))
