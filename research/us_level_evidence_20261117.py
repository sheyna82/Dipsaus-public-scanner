"""Fail-closed independent technical level evidence. No trading clearance."""
from datetime import datetime, timezone
import math

def fresh(stamp, now=None, max_age=900):
    now = now or datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        return dt.tzinfo is not None and -30 <= (now-dt).total_seconds() <= max_age
    except (AttributeError, TypeError, ValueError, OverflowError):
        return False

def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0

def assess_levels(quote, resistance, invalidation, now=None):
    """Inputs are independently sourced evidence dicts: value, source, checked_utc, verified."""
    missing = []
    for name, item in (("quote", quote), ("resistance", resistance), ("invalidation", invalidation)):
        if not isinstance(item, dict) or not positive(item.get("value")):
            missing.append(name + "_VALUE")
            continue
        if not item.get("source") or not fresh(item.get("checked_utc"), now):
            missing.append(name + "_PROVENANCE_OR_FRESHNESS")
        if item.get("verified") is not True:
            missing.append(name + "_UNVERIFIED")
    if missing:
        return {"status": "UNKNOWN", "blocks": sorted(set(missing)), "trade_ready": False}
    entry, target, stop = quote["value"], resistance["value"], invalidation["value"]
    if not stop < entry < target:
        return {"status": "BLOCK", "blocks": ["INVALID_LEVEL_ORDER"], "trade_ready": False}
    if resistance["source"] == "route_2_break_above" or invalidation["source"] == "route_2_hold_zone":
        return {"status": "BLOCK", "blocks": ["DISCOVERY_PIVOT_NOT_INDEPENDENT"], "trade_ready": False}
    return {"status": "RESEARCH_LEVELS_VERIFIED", "entry": entry, "target": target,
            "invalidation": stop, "blocks": [], "trade_ready": False}
