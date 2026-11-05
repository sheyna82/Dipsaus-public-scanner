"""Research-only event monitoring decisions; never emit orders or push notifications.

A future live integration must verify fresh market data and event provenance.
"""


def classify_event_observation(observation):
    if not isinstance(observation, dict):
        return {"status": "DATA_BLOCKED", "reason": "invalid_observation"}
    required = ("symbol", "event_id", "event_phase", "quote_fresh",
                "event_verified", "trend_confirmed", "downside_warning")
    if any(key not in observation for key in required):
        return {"status": "DATA_BLOCKED", "reason": "missing_fields"}
    if observation["event_phase"] not in ("PRE_EVENT", "POST_EVENT"):
        return {"status": "DATA_BLOCKED", "reason": "invalid_event_phase"}
    if observation["quote_fresh"] is not True or observation["event_verified"] is not True:
        return {"status": "DATA_BLOCKED", "reason": "stale_or_unverified"}
    if observation["downside_warning"] is True:
        decision = "RISK_ELEVATED"
    elif observation["event_phase"] == "POST_EVENT" and observation["trend_confirmed"] is True:
        decision = "REVIEW_ENTRY"
    else:
        decision = "WAIT_CONFIRMATION"
    return {"status": "RESEARCH_ONLY", "classification": decision,
            "symbol": observation["symbol"], "event_id": observation["event_id"],
            "notification_ready": False, "trade_ready": False}


def deduplication_key(observation):
    """Collapse research and company-event variants of the same verified event."""
    if not isinstance(observation, dict):
        return None
    symbol = observation.get("symbol")
    event_id = observation.get("event_id")
    if not isinstance(symbol, str) or not symbol.strip():
        return None
    if not isinstance(event_id, str) or not event_id.strip():
        return None
    return symbol.strip().upper() + ":" + event_id.strip()
