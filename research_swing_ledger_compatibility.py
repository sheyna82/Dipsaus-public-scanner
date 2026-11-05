"""Read-only compatibility inspection of frozen prospective ledger candidates.

The frozen momentum protocol's candidate is a binary 4-close relative momentum
observation, NOT a ranked swing trade. It cannot safely be transformed into a
priced 3/5/10-session trade without additional independently sourced fields.
"""
from datetime import date
from decimal import Decimal, InvalidOperation


def inspect_momentum_candidate(record):
    if not isinstance(record, dict):
        raise ValueError("invalid_candidate")
    required = ("protocol_id", "symbol", "signal_session",
                "signal_positive_past_excess", "past_stock_return",
                "past_spy_return", "future_outcome",
                "future_outcome_available", "research_only", "trade_ready",
                "input_verified_independently")
    if any(key not in record for key in required):
        raise ValueError("missing_frozen_candidate_field")
    if not all(isinstance(record[key], str) and record[key].strip()
               for key in ("protocol_id", "symbol")):
        raise ValueError("invalid_identity")
    date.fromisoformat(record["signal_session"])
    if not isinstance(record["signal_positive_past_excess"], bool):
        raise ValueError("invalid_binary_signal")
    try:
        stock = Decimal(str(record["past_stock_return"]))
        spy = Decimal(str(record["past_spy_return"]))
    except (InvalidOperation, ValueError):
        raise ValueError("invalid_return") from None
    if not stock.is_finite() or not spy.is_finite():
        raise ValueError("invalid_return")
    if record["signal_positive_past_excess"] != (stock > spy):
        raise ValueError("inconsistent_binary_signal")
    if record["research_only"] is not True or record["trade_ready"] is not False:
        raise ValueError("unsafe_live_candidate")
    if record["future_outcome_available"] is not False or record["future_outcome"] is not None:
        raise ValueError("candidate_contains_future_outcome")
    return {"research_only": True, "compatible_as_binary_momentum_observation": True,
            "eligible_for_swing_portfolio": False,
            "missing_for_swing": [
                "independently_verified_score_source_time",
                "continuous_rank_score",
                "execution_entry_price",
                "completed_future_session_prices",
                "transaction_cost_model",
                "verified_outcome_source_time",
            ],
            "reason": "frozen_momentum_protocol_is_not_swing_execution_protocol"}
