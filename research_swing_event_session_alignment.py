"""Fail-closed session alignment for offline event studies; no trading signals."""
from datetime import datetime, timezone
from research_swing_event_dataset_audit import audit_event_record, _utc


def align_event_to_sessions(event, sessions, *, decision_lag_seconds=0):
    """Return earliest session whose close follows verified news availability.

    Sessions contain timezone-aware 'open_at' and 'close_at' ISO timestamps.
    The decision is at the session close; any simulated entry must be later.
    """
    if type(decision_lag_seconds) not in (int, float) or not 0 <= decision_lag_seconds <= 86400:
        raise ValueError("invalid_decision_lag")
    from datetime import timedelta
    audit = audit_event_record(event)
    if not audit["research_eligible"]:
        raise ValueError("unverified_release_time")
    available = _utc(audit["available_at_utc"]) + timedelta(seconds=decision_lag_seconds)
    previous_close = None
    for index, session in enumerate(sessions):
        opening = _utc(session["open_at"])
        closing = _utc(session["close_at"])
        if opening >= closing or (previous_close is not None and opening <= previous_close):
            raise ValueError("invalid_session_order")
        previous_close = closing
        if available <= closing:
            return {"known_session_index": index, "available_at_utc": available.isoformat(),
                    "decision_at_utc": closing.isoformat(), "trade_ready": False}
    return None
