"""Research-only event-watch transition filter; no notifications or broker actions."""


def evaluate_transition(previous, current):
    """Only meaningful verified classification changes may become review candidates.

    This deliberately does not send anything and is not a live dedupe ledger.
    """
    if not isinstance(current, dict) or current.get("status") != "RESEARCH_ONLY":
        return {"status": "SUPPRESSED", "reason": "unverified_current"}
    if current.get("classification") not in (
            "WAIT_CONFIRMATION", "REVIEW_ENTRY", "RISK_ELEVATED"):
        return {"status": "SUPPRESSED", "reason": "invalid_classification"}
    if not isinstance(previous, dict):
        return {"status": "SUPPRESSED", "reason": "no_verified_baseline"}
    if previous.get("status") != "RESEARCH_ONLY":
        return {"status": "SUPPRESSED", "reason": "unverified_baseline"}
    if (previous.get("symbol"), previous.get("event_id")) != (
            current.get("symbol"), current.get("event_id")):
        return {"status": "SUPPRESSED", "reason": "different_event"}
    if previous.get("classification") == current.get("classification"):
        return {"status": "SUPPRESSED", "reason": "unchanged"}
    if current["classification"] == "WAIT_CONFIRMATION":
        return {"status": "SUPPRESSED", "reason": "wait_is_not_actionable"}
    return {"status": "REVIEW_CANDIDATE", "reason": "meaningful_transition",
            "classification": current["classification"],
            "notification_sent": False, "trade_ready": False}
