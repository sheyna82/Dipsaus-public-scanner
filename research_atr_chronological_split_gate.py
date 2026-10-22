"""Chronological split and embargo audit for offline ATR events.

Uses exchange-session indices supplied by the caller; calendar days are not
interchangeable with trading sessions. Structural checks are not provenance proof.
"""
from datetime import date


def audit_chronological_split(training, holdout, sessions, *, embargo_sessions=10):
    errors = []
    if type(embargo_sessions) is not int or embargo_sessions < 10:
        errors.append("embargo_below_10_sessions")
    if not isinstance(sessions, (list, tuple)) or not sessions:
        errors.append("invalid_session_calendar")
        sessions = []
    try:
        parsed = [date.fromisoformat(x) for x in sessions]
        if len(set(parsed)) != len(parsed) or parsed != sorted(parsed):
            errors.append("unordered_or_duplicate_sessions")
    except (TypeError, ValueError):
        errors.append("invalid_session_calendar")
    indices = {day: i for i, day in enumerate(sessions)}
    groups = {}
    for name, rows in (("training", training), ("holdout", holdout)):
        if not isinstance(rows, (list, tuple)) or not rows:
            errors.append("missing_" + name)
            continue
        dates = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("signal_date"), str):
                errors.append("invalid_" + name + "_event")
                continue
            signal = row["signal_date"]
            if signal not in indices:
                errors.append("signal_outside_calendar")
            else:
                dates.append(indices[signal])
        groups[name] = dates
    if groups.get("training") and groups.get("holdout"):
        if max(groups["training"]) >= min(groups["holdout"]):
            errors.append("chronology_overlap")
        elif min(groups["holdout"]) - max(groups["training"]) <= embargo_sessions:
            errors.append("embargo_not_satisfied")
    return {"status": "DATA_BLOCKED" if errors else "STRUCTURAL_REVIEW_ONLY",
            "errors": sorted(set(errors)), "independent_holdout_verified": False,
            "trade_ready": False, "exchange_calendar_verified": False}
