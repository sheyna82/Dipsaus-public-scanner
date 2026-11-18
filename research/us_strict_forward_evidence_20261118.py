"""Strict prospective breakout evidence gate.

Requires snapshot close below friction and a later *completed* bar whose end
precedes its observation time. An already-broken level is not a new breakout.
No broker or provider access, no trades or production integration.
"""
from datetime import datetime, timezone
from research.us_breakout_retest_shadow_20261118 import audit_breakout_retest

def _time(v):
    if not isinstance(v, str):
        return None
    try:
        d = datetime.fromisoformat(v.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError, OverflowError):
        return None

def evaluate_strict_forward(snapshot_result, completed_bars):
    base = {"status": "BLOCKED", "trade_ready": False, "notify": False,
            "automatic_orders": False, "order_placement_enabled": False,
            "research_only": True}
    if not isinstance(snapshot_result, dict) or snapshot_result.get("status") != "WATCH_UNVERIFIED":
        return {**base, "blocks": ["SNAPSHOT_UNVERIFIED"]}
    snap = snapshot_result.get("snapshot")
    if not isinstance(snap, dict) or not isinstance(completed_bars, list):
        return {**base, "blocks": ["INPUT_INVALID"]}
    cutoff = _time(snap.get("decision_observed_utc"))
    last_bar = _time(snap.get("source_last_bar_utc"))
    level, baseline = snap.get("historical_friction_usd"), snap.get("historical_close_usd")
    if (cutoff is None or last_bar is None or last_bar > cutoff
            or any(type(x) not in (int, float) or not 0 < x < float("inf")
                   for x in (level, baseline))):
        return {**base, "blocks": ["SNAPSHOT_EVIDENCE_INVALID"]}
    if baseline >= level:
        return {**base, "status": "BASELINE_ALREADY_AT_OR_ABOVE_FRICTION",
                "blocks": ["NO_NEW_CROSS_FROM_BELOW"]}
    if not completed_bars:
        return {**base, "status": "NO_FORWARD_EVIDENCE", "blocks": ["NO_COMPLETED_BARS"]}
    prev_end, prev_observed = last_bar, cutoff
    observations = []
    for i, bar in enumerate(completed_bars):
        if not isinstance(bar, dict):
            return {**base, "blocks": ["BAR_INVALID"], "invalid_index": i}
        end, observed = _time(bar.get("bar_end_utc")), _time(bar.get("observed_utc"))
        price = bar.get("close_usd")
        if (end is None or observed is None or end <= prev_end or
                observed <= prev_observed or end > observed or
                end <= cutoff or type(price) not in (int, float) or
                not 0 < price < float("inf")):
            return {**base, "blocks": ["BAR_TIME_OR_PRICE_INVALID"], "invalid_index": i}
        observations.append({"observed_utc": bar["observed_utc"], "close_usd": price})
        prev_end, prev_observed = end, observed
    result = audit_breakout_retest({"symbol": snap.get("symbol"),
                                    "historical_friction_usd": level,
                                    "observations": observations})
    return {**base, "status": "STRICT_FORWARD_RESEARCH_ONLY" if result["status"] != "BLOCKED" else "BLOCKED",
            "pattern_status": result["status"], "observation_count": len(observations),
            "blocks": sorted(set(result["blocks"] + ["SOURCE_AUTHENTICITY_NOT_ATTESTED",
                                                   "BROKER_EXECUTION_UNVERIFIED"])),
            "limitations": ["Completed bar and observation times supplied, not independently attested",
                            "No execution or profitability inference"]}
