"""Offline audit of historical signal coverage before any backtest conclusions.

Requires a declared signal universe (including rejected signals), not merely
the profitable subset. Completeness is never self-attested as verified.
"""
from datetime import datetime, timezone

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}

def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except ValueError:
        return None

def audit_historical_coverage(signals, outcomes):
    if not isinstance(signals, list) or not isinstance(outcomes, list):
        return {**BLOCKED, "status": "COVERAGE_INPUT_BLOCKED",
                "reason": "INVALID_COLLECTION"}
    indexed = {}
    for signal in signals:
        if not isinstance(signal, dict) or not isinstance(signal.get("id"), str) or not signal["id"].strip():
            return {**BLOCKED, "status": "COVERAGE_INPUT_BLOCKED", "reason": "INVALID_SIGNAL"}
        if signal["id"] in indexed:
            return {**BLOCKED, "status": "COVERAGE_INPUT_BLOCKED", "reason": "DUPLICATE_SIGNAL"}
        if signal.get("decision") not in ("SELECTED", "REJECTED", "DEFERRED"):
            return {**BLOCKED, "status": "COVERAGE_INPUT_BLOCKED", "reason": "INVALID_DECISION"}
        observed = _timestamp(signal.get("observed_utc"))
        if observed is None:
            return {**BLOCKED, "status": "COVERAGE_INPUT_BLOCKED", "reason": "INVALID_SIGNAL_TIME"}
        indexed[signal["id"]] = (signal, observed)
    seen_outcomes = set()
    for outcome in outcomes:
        if not isinstance(outcome, dict) or outcome.get("id") not in indexed:
            return {**BLOCKED, "status": "COVERAGE_INPUT_BLOCKED", "reason": "ORPHAN_OUTCOME"}
        rid = outcome["id"]
        if rid in seen_outcomes:
            return {**BLOCKED, "status": "COVERAGE_INPUT_BLOCKED", "reason": "DUPLICATE_OUTCOME"}
        observed = _timestamp(outcome.get("observed_utc"))
        if observed is None or observed <= indexed[rid][1]:
            return {**BLOCKED, "status": "COVERAGE_INPUT_BLOCKED", "reason": "INVALID_OUTCOME_TIME"}
        seen_outcomes.add(rid)
    missing = sorted(set(indexed) - seen_outcomes)
    counts = {k: sum(s["decision"] == k for s, _ in indexed.values())
              for k in ("SELECTED", "REJECTED", "DEFERRED")}
    return {**BLOCKED, "status": "HISTORICAL_COVERAGE_RESEARCH_ONLY",
            "signals": len(indexed), "outcomes": len(seen_outcomes),
            "missing_outcome_ids": missing, "decision_counts": counts,
            "outcome_coverage_fraction": (
                round(len(seen_outcomes) / len(indexed), 4) if indexed else None),
            "complete_candidate_universe_verified": False,
            "source_authenticity_independently_verified": False,
            "note": "Only supplied signals counted; no claim that all scanner signals were archived."}
