"""Research-only timestamp gate for next-session swing execution.

For every simulated trade, verify that a decision uses only completed closes,
that the next open is strictly later, and that an outcome has matured before
the evaluation cutoff. UTC ISO timestamps must include an explicit offset.
This gate does not authenticate external market data.
"""
from datetime import datetime, timezone


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("invalid_timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone_required")
    return parsed.astimezone(timezone.utc)


def validate_execution_timestamps(trades, *, evaluation_cutoff):
    cutoff = _timestamp(evaluation_cutoff)
    if not isinstance(trades, (list, tuple)):
        raise ValueError("invalid_trades")
    seen = set()
    accepted = []
    for trade in trades:
        if not isinstance(trade, dict):
            raise ValueError("invalid_trade")
        identifier = trade.get("trade_id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("duplicate_or_invalid_trade")
        seen.add(identifier)
        score = _timestamp(trade.get("score_available_at"))
        decision = _timestamp(trade.get("entry_decision_at"))
        entry = _timestamp(trade.get("entry_execution_at"))
        exit_decision = _timestamp(trade.get("exit_decision_at"))
        exit_execution = _timestamp(trade.get("exit_execution_at"))
        if not (score <= decision < entry < exit_decision < exit_execution <= cutoff):
            raise ValueError("lookahead_or_unmatured_outcome")
        accepted.append(identifier)
    return {"research_only": True, "trade_ready": False,
            "source_timestamps_independently_attested": False,
            "evaluation_cutoff": cutoff.isoformat(),
            "accepted_trade_ids": accepted}
