"""Spoor 2: isolated technical-level evidence audit.

Never verifies a market level merely because a flag says 'verified'. Requires
independent provenance, freshness and a coherent price structure. This audit
returns research readiness only; it never authorizes a trade or ntfy send.
"""
from datetime import datetime, timezone
import math


def _price(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0


def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo else None


def audit_levels(evidence, *, now_utc, max_age_seconds=900):
    blocks = []
    if not isinstance(evidence, dict) or not isinstance(now_utc, datetime) or now_utc.tzinfo is None:
        return {"status": "BLOCKED", "blocks": ["INVALID_INPUT"], "trade_ready": False}
    if not isinstance(max_age_seconds, (int, float)) or isinstance(max_age_seconds, bool) or not 0 < max_age_seconds <= 86400:
        return {"status": "BLOCKED", "blocks": ["INVALID_MAX_AGE"], "trade_ready": False}
    entry = evidence.get("broker_ask_usd")
    invalidation = evidence.get("invalidation_usd")
    resistance = evidence.get("resistance_usd")
    if not all(_price(x) for x in (entry, invalidation, resistance)):
        blocks.append("MISSING_OR_INVALID_PRICE")
    elif not invalidation < entry < resistance:
        blocks.append("INVALID_PRICE_STRUCTURE")

    # The resistance and invalidation must each have their own externally
    # inspectable evidence record, not an unsubstantiated boolean or model output.
    for label in ("broker", "invalidation", "resistance"):
        item = evidence.get(label + "_evidence")
        if not isinstance(item, dict):
            blocks.append(label.upper() + "_EVIDENCE_MISSING")
            continue
        if item.get("verified") is not True:
            blocks.append(label.upper() + "_NOT_VERIFIED")
        if not isinstance(item.get("source"), str) or not item["source"].strip():
            blocks.append(label.upper() + "_SOURCE_MISSING")
        if not isinstance(item.get("source_record_id"), str) or not item["source_record_id"].strip():
            blocks.append(label.upper() + "_RECORD_MISSING")
        ts = _utc(item.get("checked_utc"))
        age = (now_utc.astimezone(timezone.utc) - ts).total_seconds() if ts else None
        if age is None or not 0 <= age <= max_age_seconds:
            blocks.append(label.upper() + "_STALE_OR_FUTURE")
        observed = item.get("observed_price_usd")
        expected = {"broker": entry, "invalidation": invalidation, "resistance": resistance}[label]
        if not _price(observed) or not _price(expected) or abs(observed - expected) > 0.000001:
            blocks.append(label.upper() + "_PRICE_MISMATCH")

    if _price(entry) and _price(invalidation) and _price(resistance) and invalidation < entry < resistance:
        rr = (resistance - entry) / (entry - invalidation)
        if rr < 2:
            blocks.append("RR_BELOW_TWO")
    else:
        rr = None
    return {
        "status": "EVIDENCE_PRESENT_REQUIRES_INDEPENDENT_REVIEW" if not blocks else "BLOCKED",
        "blocks": blocks,
        "reference_rr": round(rr, 4) if rr is not None else None,
        "trade_ready": False,
        "order_placement_enabled": False,
    }
