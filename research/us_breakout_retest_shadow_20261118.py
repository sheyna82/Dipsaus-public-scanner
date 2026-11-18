"""Offline, fail-closed breakout/retest research. Never a trading signal.

All observations must be caller-provided point-in-time evidence. Historical
friction is NOT a verified resistance level. No provider, broker or network IO.
"""
from datetime import datetime, timezone

STATES = ("WATCH_UNVERIFIED", "BREAKOUT_OBSERVED", "RETEST_OBSERVED",
          "RESEARCH_REVIEW", "BLOCKED")

def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        x = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return x.astimezone(timezone.utc) if x.tzinfo else None
    except (ValueError, OverflowError):
        return None

def audit_breakout_retest(record):
    base = {"status": "BLOCKED", "blocks": [], "trade_ready": False,
            "notify": False, "automatic_orders": False,
            "order_placement_enabled": False, "research_only": True}
    if not isinstance(record, dict):
        return {**base, "blocks": ["INVALID_RECORD"]}
    symbol = record.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        return {**base, "blocks": ["INVALID_SYMBOL"]}
    level = record.get("historical_friction_usd")
    if not isinstance(level, (int, float)) or isinstance(level, bool) or not 0 < level < float("inf"):
        return {**base, "blocks": ["INVALID_FRICTION_REFERENCE"]}
    observations = record.get("observations")
    if not isinstance(observations, list) or not observations:
        return {**base, "status": "WATCH_UNVERIFIED",
                "blocks": ["NO_POINT_IN_TIME_OBSERVATIONS"]}
    previous = None
    stages = []
    for index, obs in enumerate(observations):
        if not isinstance(obs, dict):
            return {**base, "blocks": ["INVALID_OBSERVATION"], "invalid_index": index}
        t = _utc(obs.get("observed_utc"))
        close = obs.get("close_usd")
        if t is None or (previous is not None and t <= previous):
            return {**base, "blocks": ["TIMESTAMP_MISSING_OR_NONMONOTONIC"], "invalid_index": index}
        if not isinstance(close, (int, float)) or isinstance(close, bool) or not 0 < close < float("inf"):
            return {**base, "blocks": ["INVALID_OBSERVED_CLOSE"], "invalid_index": index}
        previous = t
        stages.append((t, close))
    breakout = next((i for i, (_, close) in enumerate(stages) if close > level), None)
    if breakout is None:
        return {**base, "status": "WATCH_UNVERIFIED",
                "blocks": ["BREAKOUT_NOT_OBSERVED", "RESISTANCE_UNVERIFIED"]}
    # A retest requires a *later* observation touching the level, and a
    # subsequent reclaim. Same-bar high/low cannot establish event order.
    touch = next((i for i in range(breakout + 1, len(stages))
                  if stages[i][1] <= level), None)
    if touch is None:
        return {**base, "status": "BREAKOUT_OBSERVED",
                "blocks": ["RETEST_NOT_OBSERVED", "RESISTANCE_UNVERIFIED"]}
    reclaim = next((i for i in range(touch + 1, len(stages))
                    if stages[i][1] > level), None)
    if reclaim is None:
        return {**base, "status": "RETEST_OBSERVED",
                "blocks": ["RECLAIM_NOT_OBSERVED", "RESISTANCE_UNVERIFIED"]}
    # Historical levels, unverified invalidation, execution and net EUR
    # economics must never be promoted to an executable buy.
    return {**base, "status": "RESEARCH_REVIEW",
            "blocks": ["RESISTANCE_UNVERIFIED", "INVALIDATION_UNVERIFIED",
                       "BROKER_QUOTE_UNVERIFIED", "EUR_NET_PROFIT_UNVERIFIED",
                       "RISK_REWARD_UNVERIFIED", "COMPANY_EVENT_UNVERIFIED"],
            "breakout_observed_utc": observations[breakout]["observed_utc"],
            "touch_observed_utc": observations[touch]["observed_utc"],
            "reclaim_observed_utc": observations[reclaim]["observed_utc"]}
