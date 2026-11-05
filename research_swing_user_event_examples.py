"""Frozen user-observed event/recovery examples for offline regression research.

Dates are alert claims, NOT verified publication timestamps. No return labels,
trade signals, event surprises, or prices are inferred from these examples.
"""
EXAMPLES = (
    {"symbol": "AMD", "alert_type": "event_calendar", "claimed_date": "2026-11-03", "status": "unverified"},
    {"symbol": "AMZN", "alert_type": "event_calendar", "claimed_date": "2026-10-29", "status": "unverified"},
    {"symbol": "PLTR", "alert_type": "event_calendar", "claimed_date": "2026-11-02", "status": "unverified"},
    {"symbol": "COHU", "alert_type": "event_calendar", "claimed_date": "2026-10-28", "status": "unverified"},
    {"symbol": "COHU", "alert_type": "event_calendar", "claimed_date": "2026-10-28", "status": "unverified"},
    {"symbol": "MC.PA", "alert_type": "recovery_watch", "reported_score": 3, "status": "unverified"},
    {"symbol": "VIE.PA", "alert_type": "recovery_watch", "reported_score": 5, "status": "unverified"},
)

def summarize_examples():
    """Keep separate event and recovery families; count duplicate event alerts."""
    events = [e for e in EXAMPLES if e["alert_type"] == "event_calendar"]
    recovery = [e for e in EXAMPLES if e["alert_type"] == "recovery_watch"]
    distinct_events = {(e["symbol"], e["claimed_date"]) for e in events}
    return {"event_alert_count": len(events), "distinct_event_count": len(distinct_events),
            "duplicate_event_alert_count": len(events) - len(distinct_events),
            "recovery_watch_count": len(recovery), "trade_ready": False}
