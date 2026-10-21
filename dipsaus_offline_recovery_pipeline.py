"""Offline end-to-end recovery research on caller-supplied point-in-time snapshots.

No market feed, training, probabilities, order execution or live alerts.
"""
from dipsaus_offline_asof_audit import audit_asof_features
from dipsaus_offline_recovery_baseline import score_recovery_candidate
from dipsaus_offline_recovery_outcomes import evaluate_recovery_path
from dipsaus_offline_recovery_score_report import summarize_recovery_scores


def evaluate_recovery_research(observations, minimum_resolved=20, horizon=10):
    if not isinstance(observations, (list, tuple)) or type(horizon) is not int or horizon < 1:
        return None
    rows = []
    seen = set()
    exclusions = []
    for obs in observations:
        if not isinstance(obs, dict):
            return None
        ident = obs.get("id")
        if not isinstance(ident, str) or not ident or ident in seen:
            return None
        seen.add(ident)
        audit = audit_asof_features(obs.get("signal_time"), obs.get("provenance"))
        if audit is None or not audit["asof_pass"]:
            exclusions.append({"id": ident, "reason": "asof_unverified"})
            continue
        score = score_recovery_candidate(obs.get("features"))
        if score is None or score["decision"] == "ABSTAIN":
            exclusions.append({"id": ident, "reason": "score_abstained"})
            continue
        outcome = evaluate_recovery_path(obs.get("bars"), horizon=horizon)
        if outcome is None:
            exclusions.append({"id": ident, "reason": "invalid_price_path"})
            continue
        rows.append({"id": ident, "score": score["score"], "status": outcome["status"],
                     "decision": score["decision"], "outcome": outcome})
    report = summarize_recovery_scores(rows, minimum_resolved=minimum_resolved)
    if report is None:
        return None
    return {"score_report": report, "evaluated": rows, "excluded": exclusions,
            "nominated": len(observations), "included": len(rows),
            "research_only": True, "trade_ready": False, "order_instruction": None,
            "limitations": "Caller-attested as-of timestamps; no verified historical market feed, no execution, no out-of-sample validation."}
