"""DIPSAUS unified research gates: no new notifications or trading instructions.

All inputs must be supplied by verified upstream modules. Missing evidence never
becomes a pass. Research labels must not be treated as buy/sell clearance.
"""
from datetime import datetime, timezone

GATES = ("market_regime", "early_recovery", "volume_confirmation",
         "sector_rotation", "economic_calendar", "false_breakout",
         "relative_strength", "liquidity_execution", "portfolio_risk",
         "profit_extension")

def evaluate(candidate, evidence, now=None):
    now = now or datetime.now(timezone.utc)
    checks = {}
    for gate in GATES:
        item = evidence.get(gate)
        if not isinstance(item, dict):
            checks[gate] = {"status": "UNKNOWN", "reason": "UPSTREAM_NOT_CONNECTED"}
            continue
        status = item.get("status")
        stamp = item.get("checked_utc")
        fresh = False
        if isinstance(stamp, str):
            try:
                checked = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                age = (now - checked).total_seconds()
                fresh = checked.tzinfo is not None and -30 <= age <= 900
            except (ValueError, OverflowError):
                pass
        checks[gate] = {"status": status if fresh and status in ("PASS", "CAUTION", "BLOCK") else "UNKNOWN",
                        "reason": "UPSTREAM_RESEARCH" if fresh else "STALE_OR_UNVERIFIED"}
    blocks = [g for g, v in checks.items() if v["status"] == "BLOCK"]
    unknown = [g for g, v in checks.items() if v["status"] == "UNKNOWN"]
    return {"symbol": candidate.get("symbol"), "checks": checks,
            "research_status": "BLOCKED_RESEARCH" if blocks else "INCOMPLETE_RESEARCH" if unknown else "REVIEW_REQUIRED",
            "blocked_gates": blocks, "unknown_gates": unknown,
            "trade_ready": False, "notify": False, "automatic_orders": False,
            "note": "Independent DIPSAUS entry, exit, event, money and broker gates remain authoritative."}
