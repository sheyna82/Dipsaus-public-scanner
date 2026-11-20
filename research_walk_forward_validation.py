"""Offline walk-forward evaluation of research scores, not a return forecast.

Requires precomputed historical records with an as-of timestamp, future outcome
timestamp and a fixed cutoff. Never uses outcomes for scoring or trade approval.
"""
from datetime import datetime, timezone
import math
from research_candidate_review import review_research_candidates

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}

def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t.astimezone(timezone.utc) if t.tzinfo is not None else None

def evaluate_walk_forward(records, *, cutoff_utc):
    cutoff = _utc(cutoff_utc)
    if cutoff is None or not isinstance(records, list):
        return {**BLOCKED, "status": "HISTORICAL_INPUT_BLOCKED",
                "reason": "INVALID_CUTOFF_OR_RECORDS"}
    seen = set()
    prepared = []
    for record in records:
        if not isinstance(record, dict):
            return {**BLOCKED, "status": "HISTORICAL_INPUT_BLOCKED",
                    "reason": "INVALID_RECORD"}
        rid = record.get("id")
        observed = _utc(record.get("features_observed_utc"))
        outcome_at = _utc(record.get("outcome_observed_utc"))
        outcome = record.get("outcome_return_pct")
        if (not isinstance(rid, str) or not rid.strip() or rid in seen
                or observed is None or outcome_at is None
                or observed >= outcome_at
                or type(outcome) not in (int, float) or not math.isfinite(outcome)):
            return {**BLOCKED, "status": "HISTORICAL_INPUT_BLOCKED",
                    "reason": "INVALID_ID_TIME_OR_OUTCOME"}
        seen.add(rid)
        features = record.get("features")
        if not isinstance(features, dict) or features.get("id") != rid:
            return {**BLOCKED, "status": "HISTORICAL_INPUT_BLOCKED",
                    "reason": "FEATURE_ID_MISMATCH"}
        # Require the complete outcome to be on the same side of the cutoff
        # as the features. This excludes outcomes spanning the split.
        if observed < cutoff <= outcome_at:
            partition = "EXCLUDED_CROSS_CUTOFF"
        elif outcome_at < cutoff:
            partition = "TRAIN"
        else:
            partition = "TEST"
        prepared.append((rid, features, outcome, partition))
    result = review_research_candidates([p[1] for p in prepared])
    if result["status"] != "RESEARCH_REVIEW_ONLY":
        return {**BLOCKED, "status": "HISTORICAL_INPUT_BLOCKED",
                "reason": "CANDIDATE_REVIEW_BLOCKED"}
    ranked = {c["id"]: c for c in result["candidates"]}
    summaries = {}
    for partition in ("TRAIN", "TEST"):
        rows = [(ranked[rid], outcome) for rid, _, outcome, part in prepared
                if part == partition]
        selected = [(r, outcome) for r, outcome in rows
                    if r["eligible_for_further_research"]]
        summaries[partition.lower()] = {
            "observations": len(rows),
            "research_review_candidates": len(selected),
            "mean_observed_return_pct": (
                round(sum(outcome for _, outcome in selected) / len(selected), 4)
                if selected else None),
            "positive_outcome_fraction": (
                round(sum(outcome > 0 for _, outcome in selected) / len(selected), 4)
                if selected else None)}
    return {**BLOCKED, "status": "HISTORICAL_RESEARCH_ONLY",
            "cutoff_utc": cutoff.isoformat(),
            "train": summaries["train"], "test": summaries["test"],
            "excluded_cross_cutoff": sum(p[3] == "EXCLUDED_CROSS_CUTOFF" for p in prepared),
            "sample_sufficiency_verified": False,
            "source_authenticity_independently_verified": False,
            "note": "Unverified supplied outcomes; no calibration or execution assumptions."}
