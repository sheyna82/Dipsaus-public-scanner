"""Pure offline point-in-time gate for the six-event research cohort.

No market data fetch, forecasting, notifications, or trading.
"""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from research_event_opportunity_cohort import EVENT_COHORT

EVENT_DATES = dict(EVENT_COHORT)


def audit_event_snapshot(symbol, captured_at_utc, event_date, close_price,
                         benchmark_close, source, as_of_date):
    """Check a frozen pre-event observation; never certify vendor authenticity."""
    if symbol not in EVENT_DATES or event_date != EVENT_DATES[symbol]:
        raise ValueError("unknown_or_mismatched_event")
    try:
        timestamp = datetime.fromisoformat(captured_at_utc.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError("invalid_snapshot_timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("snapshot_timestamp_requires_timezone")
    captured = timestamp.astimezone(timezone.utc)
    reference = date.fromisoformat(as_of_date)
    if captured.date() > reference:
        raise ValueError("snapshot_after_as_of_date")
    # Date-level pre-event rule is conservative; actual release time may
    # differ by issuer and must be verified before finer-grained analysis.
    if captured.date() >= date.fromisoformat(event_date):
        raise ValueError("snapshot_not_strictly_before_event_date")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("missing_snapshot_source")
    try:
        price = Decimal(str(close_price))
        benchmark = Decimal(str(benchmark_close))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("invalid_snapshot_price") from exc
    if not all(x.is_finite() and x > 0 for x in (price, benchmark)):
        raise ValueError("invalid_snapshot_price")
    return {
        "symbol": symbol, "event_date": event_date,
        "captured_at_utc": captured.isoformat(),
        "as_of_date": reference.isoformat(),
        "close_price": str(price), "benchmark_close": str(benchmark),
        "declared_source": source.strip(),
        "snapshot_temporally_valid": True,
        "source_authenticity_verified": False,
        "issuer_event_time_verified": False,
        "prediction_issued": False,
        "trade_ready": False,
    }
