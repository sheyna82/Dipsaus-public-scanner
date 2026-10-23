"""Offline point-in-time earnings availability gate for historical research.

Never use an earnings event announced or revised after the signal's as-of time.
This gate only checks caller-provided timestamp consistency; it does not verify
a vendor's archival integrity or guarantee completeness of earnings coverage.
"""
from datetime import datetime, timezone


def _aware(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() is None:
            return None
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def audit_earnings_asof(signal_time, earnings_records, *, coverage_start=None,
                       coverage_end=None):
    signal = _aware(signal_time)
    start, end = _aware(coverage_start), _aware(coverage_end)
    if signal is None or start is None or end is None or start > signal or end < signal:
        return {"status": "DATA_BLOCKED", "reason": "unverified_coverage_window",
                "trade_ready": False}
    if not isinstance(earnings_records, (list, tuple)):
        return {"status": "DATA_BLOCKED", "reason": "invalid_records", "trade_ready": False}
    visible = []
    future_publications = 0
    for record in earnings_records:
        if not isinstance(record, dict):
            return {"status": "DATA_BLOCKED", "reason": "invalid_record", "trade_ready": False}
        published = _aware(record.get("published_at"))
        event = _aware(record.get("scheduled_event_at"))
        if published is None or event is None or not isinstance(record.get("issuer_id"), str) or not record["issuer_id"]:
            return {"status": "DATA_BLOCKED", "reason": "invalid_record_timestamps",
                    "trade_ready": False}
        if published > signal:
            future_publications += 1
            continue
        if event > signal:
            visible.append({"issuer_id": record["issuer_id"],
                            "scheduled_event_at": event.isoformat(),
                            "published_at": published.isoformat()})
    visible.sort(key=lambda row: (row["scheduled_event_at"], row["issuer_id"]))
    return {"status": "ASOF_ATTESTATION_ONLY", "visible_upcoming_events": visible,
            "excluded_future_publications": future_publications,
            "coverage_window_attested": True,
            "vendor_archival_integrity_verified": False,
            "calendar_completeness_verified": False,
            "trade_ready": False}
