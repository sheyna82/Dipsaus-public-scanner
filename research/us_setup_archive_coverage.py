"""Research-only coverage report for archived US intraday sessions.

A provider's currently accessible 1-day window is not an historical archive.
This module assesses supplied archived sessions only; it never downloads data.
"""
from collections import Counter
from datetime import datetime, timezone
from research.us_setup_existing_chart_adapter import adapt_us_chart_rows


def audit_archive(sessions, *, expected_interval_minutes=1, min_sessions=20):
    if not isinstance(sessions, dict) or not sessions:
        return {"oos_eligible": False, "reason": "NO_ARCHIVED_SESSIONS", "session_count": 0}
    accepted, rejected = [], Counter()
    for key, rows in sorted(sessions.items()):
        if not isinstance(key, str) or "|" not in key:
            rejected["INVALID_SESSION_KEY"] += 1
            continue
        symbol, date = key.split("|", 1)
        try:
            day = datetime.fromisoformat(date).date()
        except ValueError:
            rejected["INVALID_SESSION_DATE"] += 1
            continue
        if not symbol or not isinstance(rows, list):
            rejected["INVALID_SESSION_CONTENT"] += 1
            continue
        result = adapt_us_chart_rows(rows, expected_interval_minutes=expected_interval_minutes)
        if not result["usable"]:
            rejected[result["reason"]] += 1
            continue
        if any(datetime.fromisoformat(bar["timestamp"]).astimezone(timezone.utc).date() != day
               for bar in result["bars"]):
            rejected["SESSION_DATE_MISMATCH_UTC"] += 1
            continue
        accepted.append(key)
    return {"oos_eligible": False,
            "reason": "INDEPENDENT_LABELS_AND_OOS_SPLIT_NOT_VERIFIED" if len(accepted) >= min_sessions
                      else "INSUFFICIENT_ARCHIVED_SESSIONS",
            "session_count": len(accepted), "accepted_sessions": accepted,
            "rejected_reasons": dict(rejected), "minimum_sessions": min_sessions,
            "historical_coverage_verified": False, "labels_independent_verified": False,
            "research_only": True}
