"""Research-only event watch batch runner; no external requests or notifications."""
from dipsaus_offline_event_watch import classify_event_observation, deduplication_key
from dipsaus_offline_event_transition import evaluate_transition


def evaluate_event_batch(observations, prior_by_key=None):
    """Deduplicate by verified event key, preferring the riskier classification.

    Conflicting event metadata is blocked instead of arbitrarily choosing a row.
    """
    if not isinstance(observations, list) or not isinstance(prior_by_key or {}, dict):
        return {"status": "REJECTED", "reason": "invalid_input"}
    previous = prior_by_key or {}
    grouped = {}
    blocked = []
    priority = {"WAIT_CONFIRMATION": 0, "REVIEW_ENTRY": 1, "RISK_ELEVATED": 2}
    for row in observations:
        key = deduplication_key(row)
        result = classify_event_observation(row)
        if key is None or result["status"] != "RESEARCH_ONLY":
            blocked.append({"key": key, "reason": result.get("reason", "missing_event_key")})
            continue
        if key in grouped and grouped[key]["event_phase"] != row["event_phase"]:
            blocked.append({"key": key, "reason": "conflicting_event_phase"})
            grouped[key]["conflict"] = True
            continue
        if key not in grouped or priority[result["classification"]] > priority[grouped[key]["result"]["classification"]]:
            grouped[key] = {"event_phase": row["event_phase"], "result": result,
                            "conflict": grouped.get(key, {}).get("conflict", False)}
    candidates = []
    for key, item in sorted(grouped.items()):
        if item["conflict"]:
            continue
        transition = evaluate_transition(previous.get(key), item["result"])
        if transition["status"] == "REVIEW_CANDIDATE":
            candidates.append({"key": key, "classification": transition["classification"]})
    return {"status": "RESEARCH_ONLY", "events_considered": len(grouped),
            "blocked": blocked, "review_candidates": candidates,
            "notifications_sent": 0, "trade_ready": False}
