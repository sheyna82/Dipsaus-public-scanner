"""Offline reconciliation of declared scanner-batch counts with archived signals.

A manifest is self-reported evidence only; matching counts cannot establish
that the scanner observed the entire candidate universe or authenticate data.
"""
from datetime import datetime, timezone
from research_historical_event_contract import validate_historical_events

BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "source_authenticity_independently_verified": False}

def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo is not None else None
    except ValueError:
        return None

def reconcile_batch_manifest(manifest, events):
    base = {**BLOCKED, "status": "BATCH_RECONCILIATION_BLOCKED",
            "complete_candidate_universe_verified": False}
    if not isinstance(manifest, dict) or set(manifest) != {
            "batch_id", "started_utc", "completed_utc", "expected_signal_count",
            "expected_decision_counts"}:
        return {**base, "reason": "INVALID_MANIFEST"}
    if not isinstance(manifest["batch_id"], str) or not manifest["batch_id"].strip():
        return {**base, "reason": "INVALID_BATCH_ID"}
    start, end = _utc(manifest["started_utc"]), _utc(manifest["completed_utc"])
    if start is None or end is None or start > end:
        return {**base, "reason": "INVALID_BATCH_WINDOW"}
    counts = manifest["expected_decision_counts"]
    labels = ("SELECTED", "REJECTED", "DEFERRED")
    if (not isinstance(counts, dict) or set(counts) != set(labels)
            or any(type(counts[k]) is not int or counts[k] < 0 for k in labels)
            or type(manifest["expected_signal_count"]) is not int
            or manifest["expected_signal_count"] < 0
            or sum(counts.values()) != manifest["expected_signal_count"]):
        return {**base, "reason": "INVALID_DECLARED_COUNTS"}
    validation = validate_historical_events(events)
    if validation["status"] != "HISTORICAL_EVENT_CONTRACT_RESEARCH_ONLY":
        return {**base, "reason": "INVALID_EVENT_CONTRACT",
                "event_contract_reason": validation.get("reason")}
    signals = [e for e in events if e["event_type"] == "SIGNAL"]
    if any(not start <= _utc(e["observed_utc"]) <= end for e in signals):
        return {**base, "reason": "SIGNAL_OUTSIDE_BATCH_WINDOW"}
    observed = {k: sum(e["decision"] == k for e in signals) for k in labels}
    match = (len(signals) == manifest["expected_signal_count"]
             and observed == counts)
    return {**BLOCKED, "status": "BATCH_COUNTS_MATCH_SELF_REPORTED" if match
            else "BATCH_COUNT_MISMATCH",
            "declared_signal_count": manifest["expected_signal_count"],
            "observed_signal_count": len(signals),
            "declared_decision_counts": dict(counts),
            "observed_decision_counts": observed,
            "count_match": match,
            "complete_candidate_universe_verified": False,
            "manifest_independently_attested": False,
            "note": "Only reconciles caller-supplied metadata; no independent scanner attestation."}
