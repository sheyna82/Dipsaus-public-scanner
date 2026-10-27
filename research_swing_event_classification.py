"""Offline event materiality and tradability research; never an order signal.

Event dates alone carry no realized surprise. Scores are descriptive
research features, not calibrated probabilities or buy recommendations.
"""
from math import isfinite

KINDS = {
    "earnings_calendar": "calendar",
    "earnings_release": "material",
    "guidance_change": "material",
    "profit_warning": "material",
    "merger_announcement": "material",
    "regulatory_decision": "material",
    "contract_announcement": "material",
    "management_change": "material",
    "other_press_release": "calendar",
}

def classify_event(event):
    """Classify a timestamped event without looking at future price candles.

    Requires an immutable event identifier and publication timestamp.
    Missing numeric surprises are unknown, not zero surprise.
    """
    kind = event["kind"]
    if kind not in KINDS:
        raise ValueError("unknown_event_kind")
    if not event.get("symbol") or not event.get("published_at") or not event.get("event_id"):
        raise ValueError("missing_event_identity")
    surprise = event.get("surprise_pct")
    if surprise is not None and (not isinstance(surprise, (int, float)) or
                                not isfinite(surprise)):
        raise ValueError("invalid_surprise")
    stage = KINDS[kind]
    if stage == "calendar":
        return {"stage": "calendar", "impact_score": None,
                "swing_score": None, "trade_ready": False}
    # Even a material announcement does not imply positive expected returns.
    return {"stage": "material", "impact_score": None,
            "swing_score": None, "trade_ready": False,
            "surprise_pct": surprise}

def deduplicate_events(events):
    """Preserve first observation; deduplicate by symbol, event id and kind."""
    seen = set()
    result = []
    for event in events:
        key = (event.get("symbol"), event.get("event_id"), event.get("kind"))
        if key not in seen:
            result.append(event)
            seen.add(key)
    return result
