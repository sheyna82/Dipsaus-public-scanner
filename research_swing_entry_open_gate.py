"""Research-only evidence gate for modeled next-open entry fills.

A score must be known before the entry decision; an entry must use the
*following* timestamped open, not the decision close. Explicit, independently
attested data remains a separate prerequisite. No network or live trading.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


def _time(value):
    if not isinstance(value, str):
        raise ValueError("invalid_market_timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("invalid_market_timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone_required")
    return parsed.astimezone(timezone.utc)


def _price(value):
    if isinstance(value, bool):
        raise ValueError("invalid_entry_open")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_entry_open") from None
    if not result.is_finite() or result <= 0:
        raise ValueError("invalid_entry_open")
    return result


def validate_next_open_entries(candidates):
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise ValueError("empty_entry_cohort")
    seen = set()
    accepted = []
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("invalid_entry_candidate")
        ticker = item.get("ticker")
        if not isinstance(ticker, str) or not ticker.strip() or ticker in seen:
            raise ValueError("duplicate_or_invalid_ticker")
        seen.add(ticker)
        score = _time(item.get("score_available_at"))
        decision = _time(item.get("entry_decision_at"))
        execution = _time(item.get("entry_execution_at"))
        observed_open = _time(item.get("entry_open_timestamp"))
        if not (score <= decision < execution == observed_open):
            raise ValueError("entry_lookahead_or_mismatched_open")
        price = _price(item.get("entry_price"))
        actual_open = _price(item.get("entry_open_price"))
        if price != actual_open:
            raise ValueError("entry_price_not_next_open")
        accepted.append(ticker)
    return {
        "research_only": True, "trade_ready": False,
        "next_open_entry_validated": True,
        "source_authenticity_verified": False,
        "accepted_tickers": accepted,
    }
