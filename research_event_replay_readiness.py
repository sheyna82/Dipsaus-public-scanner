"""Fail-closed audit of missing event-replay evidence; never claims verified returns."""
from research_event_replay_intake_202610 import CASES, eligible_replay

REQUIRED = ("alert_timestamp", "timestamped_bars", "signal_snapshot",
            "alert_evidence", "price_evidence")

def audit_case(case, evidence=None):
    if case not in CASES:
        raise ValueError("unknown_event_case")
    evidence = {} if evidence is None else evidence
    if not isinstance(evidence, dict):
        raise TypeError("evidence_must_be_mapping")
    missing = [key for key in REQUIRED if not evidence.get(key)]
    ready = False
    if not missing:
        ready = eligible_replay(case, **{key: evidence[key] for key in REQUIRED})
    return {
        "ticker": case["ticker"],
        "event_date": case["event_date"],
        "event_kind": case["kind"],
        "missing_evidence": missing,
        "intake_eligible": bool(ready),
        "independently_authenticated": False,
        "performance_claim_allowed": False,
        "reason": ("missing_point_in_time_evidence" if missing else
                   "metadata_not_validated" if not ready else
                   "independent_authentication_and_out_of_sample_validation_pending"),
    }

def audit_all(evidence_by_ticker=None):
    evidence_by_ticker = evidence_by_ticker or {}
    return [audit_case(case, evidence_by_ticker.get(case["ticker"])) for case in CASES]
