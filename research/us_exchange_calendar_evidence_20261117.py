"""Offline exchange-calendar evidence gate; no bundled holiday assumptions.

Clock screening is not proof of a trading session. Only explicitly supplied,
independently verified calendar evidence may pass the calendar gate.
"""
from datetime import date, datetime, timezone

def review_exchange_calendar(record, *, session_date, now=None, max_age_days=14):
    blocks = []
    now = now or datetime.now(timezone.utc)
    if not isinstance(record, dict):
        return {"status": "UNKNOWN", "blocks": ["CALENDAR_EVIDENCE_MISSING"],
                "exchange_calendar_verified": False, "trade_ready": False}
    if not isinstance(session_date, str):
        blocks.append("SESSION_DATE_INVALID")
    else:
        try:
            day = date.fromisoformat(session_date)
        except ValueError:
            blocks.append("SESSION_DATE_INVALID")
            day = None
    if record.get("session_date") != session_date:
        blocks.append("SESSION_DATE_MISMATCH")
    if record.get("session_kind") not in ("regular", "closed", "early_close"):
        blocks.append("SESSION_KIND_UNSUPPORTED")
    if record.get("exchange") not in ("XNAS", "XNYS"):
        blocks.append("EXCHANGE_UNSUPPORTED")
    if not isinstance(record.get("source_url"), str) or not record["source_url"].startswith("https://"):
        blocks.append("SOURCE_URL_INVALID")
    if not isinstance(record.get("retrieval_reference"), str) or not record["retrieval_reference"].strip():
        blocks.append("RETRIEVAL_REFERENCE_MISSING")
    try:
        stamp = datetime.fromisoformat(record["retrieved_utc"].replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset() is None or not -30 <= (now-stamp).total_seconds() <= max_age_days*86400:
            blocks.append("RETRIEVAL_STALE_OR_INVALID")
    except (KeyError, AttributeError, TypeError, ValueError, OverflowError):
        blocks.append("RETRIEVAL_STALE_OR_INVALID")
    # Metadata can be self-declared or forged. External source verification is
    # required before this gate can be promoted to authoritative evidence.
    return {"status": "METADATA_COMPLETE_UNVERIFIED" if not blocks else "UNKNOWN",
            "blocks": sorted(set(blocks)), "exchange_calendar_verified": False,
            "trade_ready": False}
