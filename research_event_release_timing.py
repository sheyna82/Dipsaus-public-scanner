"""Offline earnings-release timing audit, with explicit uncertainty.

Event dates alone cannot identify the first tradable post-release close.
No network access, live alerts, or trading decisions.
"""
from datetime import date, datetime, timezone


def audit_event_release_timing(event_date, release_timestamp, market_close_timestamp,
                               first_followup_close_timestamp, source):
    """Validate temporal ordering, not authenticity of supplied timestamps."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("missing_release_source")

    def parse(value):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError("invalid_release_timestamp") from exc
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError("release_timezone_required")
        return result.astimezone(timezone.utc)

    release = parse(release_timestamp)
    close = parse(market_close_timestamp)
    followup = parse(first_followup_close_timestamp)
    expected_date = date.fromisoformat(event_date)
    if release.date() != expected_date:
        raise ValueError("release_date_mismatch")
    if release <= close:
        raise ValueError("not_after_market_close")
    if followup <= release or followup.date() <= close.date():
        raise ValueError("followup_not_after_release")
    if close.date() != expected_date:
        raise ValueError("market_close_event_date_mismatch")
    return {
        "event_date": event_date,
        "release_timestamp_utc": release.isoformat(),
        "market_close_timestamp_utc": close.isoformat(),
        "first_followup_close_timestamp_utc": followup.isoformat(),
        "declared_source": source.strip(),
        "temporal_order_verified": True,
        "issuer_release_source_authenticated": False,
        "exchange_calendar_verified": False,
        "event_window_trade_ready": False,
    }
