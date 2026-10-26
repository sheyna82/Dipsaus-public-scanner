"""Strict research gateway: timestamp validation before any P&L evaluation.

The supplied evaluator is called only after *every* trade has passed the
chronological gate. The gateway does not authenticate provider timestamps,
and does not claim that the evaluator uses a particular fill model.
"""
from research_swing_execution_timestamp_gate import validate_execution_timestamps


def evaluate_timestamp_gated_batch(trades, *, evaluation_cutoff, evaluator):
    if not callable(evaluator):
        raise ValueError("invalid_evaluator")
    if not isinstance(trades, (list, tuple)) or not trades:
        raise ValueError("empty_gated_batch")
    gate = validate_execution_timestamps(
        trades, evaluation_cutoff=evaluation_cutoff)
    # No partial scoring or P&L on mixed valid/invalid cohorts.
    outcome = evaluator(trades)
    return {
        "research_only": True, "trade_ready": False,
        "timestamp_gate_passed": True,
        "timestamp_attestation_verified": False,
        "evaluation_cutoff": gate["evaluation_cutoff"],
        "validated_trade_ids": gate["accepted_trade_ids"],
        "analysis": outcome,
    }
