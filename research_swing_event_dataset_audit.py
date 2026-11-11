"""Offline event dataset audit: fail closed on unverifiable timestamps.

No historical price labels or predictions are created here. This module
prevents date-only earnings calendars from masquerading as known news.
"""
from datetime import datetime, timezone

def _utc(value):
    if not isinstance(value, str):
        raise ValueError("timestamp_required")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timezone_required")
    return dt.astimezone(timezone.utc)

def audit_event_record(event):
    """Validate public-knowledge time separately from scheduled event time."""
    for field in ("symbol", "event_id", "kind", "source"):
        if not isinstance(event.get(field), str) or not event[field].strip():
            raise ValueError("missing_" + field)
    published = _utc(event.get("published_at"))
    observed = _utc(event.get("first_observed_at"))
    if observed < published:
        raise ValueError("observed_before_publication")
    available = max(published, observed)
    return {
        "symbol": event["symbol"],
        "event_id": event["event_id"],
        "kind": event["kind"],
        "source": event["source"],
        "available_at_utc": available.isoformat(),
        "has_verified_release_time": bool(event.get("release_timestamp_verified", False)),
        "research_eligible": bool(event.get("release_timestamp_verified", False)),
        "trade_ready": False,
    }

def audit_event_dataset(events):
    """Audit rows and flag duplicates; never silently drop differing revisions."""
    results = []
    seen = set()
    for event in events:
        row = audit_event_record(event)
        key = (row["symbol"], row["event_id"], row["kind"])
        row["duplicate"] = key in seen
        seen.add(key)
        results.append(row)
    return results
