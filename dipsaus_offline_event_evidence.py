"""Offline event evidence adapter: only explicit measured inputs, no invented signals."""


def build_event_observation(event, quote):
    """Translate externally verified event and quote evidence into watch inputs.

    The caller must verify source timestamps and independently derive technical
    confirmations. Missing evidence blocks evaluation. No network or live use.
    """
    if not isinstance(event, dict) or not isinstance(quote, dict):
        return {"status": "DATA_BLOCKED", "reason": "invalid_sources"}
    event_fields = ("symbol", "event_id", "event_phase", "event_verified")
    quote_fields = ("quote_fresh", "trend_confirmed", "downside_warning")
    if any(k not in event for k in event_fields) or any(k not in quote for k in quote_fields):
        return {"status": "DATA_BLOCKED", "reason": "missing_evidence"}
    if event["event_verified"] is not True or quote["quote_fresh"] is not True:
        return {"status": "DATA_BLOCKED", "reason": "unverified_or_stale"}
    if not isinstance(event["symbol"], str) or not event["symbol"].strip():
        return {"status": "DATA_BLOCKED", "reason": "invalid_symbol"}
    if not isinstance(event["event_id"], str) or not event["event_id"].strip():
        return {"status": "DATA_BLOCKED", "reason": "invalid_event_id"}
    if event["event_phase"] not in ("PRE_EVENT", "POST_EVENT"):
        return {"status": "DATA_BLOCKED", "reason": "invalid_phase"}
    if type(quote["trend_confirmed"]) is not bool or type(quote["downside_warning"]) is not bool:
        return {"status": "DATA_BLOCKED", "reason": "invalid_technical_evidence"}
    return {"symbol": event["symbol"].strip().upper(),
            "event_id": event["event_id"].strip(),
            "event_phase": event["event_phase"],
            "event_verified": True, "quote_fresh": True,
            "trend_confirmed": quote["trend_confirmed"],
            "downside_warning": quote["downside_warning"]}
