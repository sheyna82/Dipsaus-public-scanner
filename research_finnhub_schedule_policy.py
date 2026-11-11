"""Research-only schedule eligibility policy, offline and without side effects.

This is a planning gate, NOT a scheduler. It never fetches market data,
uses secrets, sends alerts, or triggers orders.
"""
from datetime import datetime, timedelta, timezone

SYMBOLS = frozenset({"AMD", "COHU", "CSGP", "AAPL"})
MAX_DAILY_OBSERVATIONS = 4
MIN_INTERVAL = timedelta(minutes=30)


def evaluate_schedule(*, symbol, now, prior_utc, daily_count, enabled=False):
    """Fail closed: require explicit enablement, UTC, rate limits and no duplicates.

    prior_utc: recorded completed observation times for this symbol, UTC.
    daily_count: total completed observations across all symbols for UTC day.
    """
    if enabled is not True:
        return {"eligible": False, "reason": "not_approved_for_automation"}
    if symbol not in SYMBOLS:
        return {"eligible": False, "reason": "unsupported_symbol"}
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() != timedelta(0):
        return {"eligible": False, "reason": "utc_required"}
    if type(daily_count) is not int or daily_count < 0 or daily_count >= MAX_DAILY_OBSERVATIONS:
        return {"eligible": False, "reason": "daily_capacity_unavailable"}
    if not isinstance(prior_utc, (list, tuple)):
        return {"eligible": False, "reason": "invalid_history"}
    for timestamp in prior_utc:
        if not isinstance(timestamp, datetime) or timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
            return {"eligible": False, "reason": "invalid_history"}
        if timestamp > now:
            return {"eligible": False, "reason": "future_observation"}
        if now - timestamp < MIN_INTERVAL:
            return {"eligible": False, "reason": "duplicate_or_too_soon"}
    return {"eligible": True, "reason": "offline_policy_only"}


def safe_default():
    return evaluate_schedule(
        symbol="AMD", now=datetime.now(timezone.utc),
        prior_utc=[], daily_count=0, enabled=False)
