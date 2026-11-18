"""Offline forward-only replay gate for prospectively recorded watch snapshots.

Requires explicitly supplied post-snapshot observations. No historical
reconstruction, provider fetches, private exports or trade authorization.
"""
from datetime import datetime, timezone
from research.us_breakout_retest_shadow_20261118 import audit_breakout_retest

def _parse(s):
    if not isinstance(s, str):
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError, OverflowError):
        return None

def replay_forward(snapshot_result, observations):
    base = {"status": "BLOCKED", "trade_ready": False, "notify": False,
            "automatic_orders": False, "order_placement_enabled": False,
            "research_only": True}
    if not isinstance(snapshot_result, dict) or snapshot_result.get("status") != "WATCH_UNVERIFIED":
        return {**base, "blocks": ["UNVERIFIED_SNAPSHOT"]}
    snapshot = snapshot_result.get("snapshot")
    if not isinstance(snapshot, dict) or not isinstance(observations, list):
        return {**base, "blocks": ["INPUT_MISSING"]}
    cutoff = _parse(snapshot.get("decision_observed_utc"))
    if cutoff is None:
        return {**base, "blocks": ["CUTOFF_INVALID"]}
    if not observations:
        return {**base, "status": "NO_FORWARD_EVIDENCE",
                "blocks": ["NO_POST_SNAPSHOT_OBSERVATIONS"]}
    for index, item in enumerate(observations):
        if not isinstance(item, dict) or _parse(item.get("observed_utc")) is None:
            return {**base, "blocks": ["FORWARD_OBSERVATION_INVALID"], "invalid_index": index}
        if _parse(item["observed_utc"]) <= cutoff:
            return {**base, "blocks": ["LOOKAHEAD_OR_PRE_SNAPSHOT_BAR"], "invalid_index": index}
    result = audit_breakout_retest({
        "symbol": snapshot.get("symbol"),
        "historical_friction_usd": snapshot.get("historical_friction_usd"),
        "observations": observations})
    return {**base, "status": "FORWARD_RESEARCH_ONLY" if result["status"] != "BLOCKED" else "BLOCKED",
            "pattern_status": result["status"],
            "blocks": sorted(set(result["blocks"] + ["SOURCE_AUTHENTICITY_NOT_ATTESTED",
                                                    "NO_EXECUTION_ECONOMICS"])),
            "observation_count": len(observations),
            "limitations": ["Forward sequence checked against supplied decision time only",
                            "Source timestamps and independent provenance not verified",
                            "No trading performance or win-rate inferred"]}
