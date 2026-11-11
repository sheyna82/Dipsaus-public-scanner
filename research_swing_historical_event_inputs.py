"""Strict, offline input gate for reproducible historical event studies.

Never download or fabricate records. Reject incomplete provenance, duplicates,
and unverified event timestamps before any outcome labeling.
"""
from datetime import datetime
from math import isfinite
from research_swing_event_dataset_audit import audit_event_record, _utc


def validate_historical_event_rows(rows, *, cutoff_at):
    """Validate event records known by cutoff; preserve their source metadata.

    A verified timestamp alone is not evidence of historical truth: source URL
    and source-observation time must be independently auditable.
    """
    cutoff = _utc(cutoff_at)
    if not isinstance(rows, (list, tuple)):
        raise ValueError("rows_must_be_sequence")
    accepted = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid_event_row")
        audit = audit_event_record(row)
        if not audit["research_eligible"]:
            raise ValueError("unverified_release_time")
        source_url = row.get("source_url")
        if not isinstance(source_url, str) or not source_url.startswith(("https://", "http://")):
            raise ValueError("missing_source_url")
        available = _utc(audit["available_at_utc"])
        if available > cutoff:
            raise ValueError("event_after_cutoff")
        key = (audit["symbol"], audit["event_id"], audit["kind"])
        if key in seen:
            raise ValueError("duplicate_event")
        seen.add(key)
        accepted.append({
            "symbol": audit["symbol"], "event_id": audit["event_id"],
            "kind": audit["kind"], "source": audit["source"],
            "source_url": source_url,
            "published_at": row["published_at"],
            "first_observed_at": row["first_observed_at"],
            "release_timestamp_verified": True,
            "available_at_utc": available.isoformat(),
            "trade_ready": False,
        })
    return accepted


def validate_daily_bars(bars):
    """Validate chronological OHLC sessions without silently sorting revisions."""
    if not isinstance(bars, (list, tuple)) or not bars:
        raise ValueError("empty_price_bars")
    previous = None
    for bar in bars:
        if not isinstance(bar, dict):
            raise ValueError("invalid_price_bar")
        opened = _utc(bar.get("open_at"))
        closed = _utc(bar.get("close_at"))
        if opened >= closed or (previous is not None and opened <= previous):
            raise ValueError("invalid_bar_order")
        previous = closed
        prices = [bar.get(k) for k in ("open", "high", "low", "close")]
        if any(type(v) not in (float, int) or not isfinite(v) or v <= 0 for v in prices):
            raise ValueError("invalid_ohlc")
        opening, high, low, closing = prices
        if low > min(opening, closing) or high < max(opening, closing) or low > high:
            raise ValueError("inconsistent_ohlc")
    return len(bars)
