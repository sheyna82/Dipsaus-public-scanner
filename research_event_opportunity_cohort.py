"""Offline, fixed-cohort event study; no quotes, network, notifications or orders.

An event date alone is never evidence of an investment opportunity.
This cohort is frozen from the 2026-10-24 user-observed notifications.
"""
from datetime import date, datetime, timezone
from event_opportunity_engine import classify_event_opportunities

EVENT_COHORT = (
    ("TSLA", "2026-10-21"),
    ("META", "2026-10-21"),
    ("COHU", "2026-10-28"),
    ("AMZN", "2026-10-29"),
    ("PLTR", "2026-11-02"),
    ("AMD", "2026-11-03"),
)
REQUIRED_EVIDENCE = (
    "issuer_confirmed_date", "fresh_quote", "quote_timestamp_utc",
    "quote_source", "price_history", "benchmark_history",
    "volume_history", "event_expectations", "release_actuals",
)
FOLLOW_UP_SESSIONS = (1, 3, 5)


def build_event_study(as_of_date="2026-10-24", evidence_by_symbol=None):
    """Produce an immutable-as-of-date research plan, not a prediction.

    Future outcomes are always unavailable; retrospectively studied events
    require timestamped pre-event evidence to avoid hindsight contamination.
    Session horizons require a verified exchange calendar.
    """
    today = date.fromisoformat(as_of_date)
    supplied = evidence_by_symbol or {}
    records = []
    for symbol, iso in EVENT_COHORT:
        event_day = date.fromisoformat(iso)
        evidence = supplied.get(symbol, {})
        if not isinstance(evidence, dict):
            raise ValueError("event_evidence_must_be_mapping")
        # A populated key is not evidence when its value is empty or unusable.
        missing = [field for field in REQUIRED_EVIDENCE
                   if field not in evidence or evidence[field] is None or
                   isinstance(evidence[field], (str, list, dict, tuple)) and
                   not evidence[field]]
        # A dated, UTC-aware snapshot is essential for future point-in-time
        # checks; do not infer its validity from a nonempty string.
        timestamp = evidence.get("quote_timestamp_utc")
        if timestamp is not None:
            try:
                parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    raise ValueError("timezone_required")
                if parsed.astimezone(timezone.utc).date() > today:
                    raise ValueError("future_quote_timestamp")
            except (ValueError, TypeError, AttributeError):
                if "quote_timestamp_utc" not in missing:
                    missing.append("quote_timestamp_utc")
        stages = [item["stage"] for item in classify_event_opportunities(iso, today)]
        records.append({
            "symbol": symbol,
            "event_date": iso,
            "as_of_date": today.isoformat(),
            "event_phase": "RETROSPECTIVE" if event_day < today else
                           "EVENT_DAY" if event_day == today else "PROSPECTIVE",
            "research_stages": stages,
            "missing_evidence": missing,
            "pre_event_snapshot_verified": False,
            "outcome_horizons_trading_sessions": list(FOLLOW_UP_SESSIONS),
            "exchange_calendar_verified": False,
            "outcomes_measured": False,
            "prediction_issued": False,
            "trade_ready": False,
        })
    return {"cohort": "event_notifications_2026_10_24",
            "as_of_date": today.isoformat(), "records": records,
            "live_notifications_enabled": False, "automatic_orders": False}
