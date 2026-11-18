"""Prospective US breakout watch snapshot contract; offline and fail-closed.

Pure function, no IO. Captures ONLY caller-supplied evidence. A run timestamp
does not attest source observation time. Never exports private candidate data.
"""
from datetime import datetime, timezone

def _parse(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError, OverflowError):
        return None

def build_watch_snapshot(candidate, *, source_observed_utc, decision_observed_utc,
                         source_last_bar_utc, batch_index):
    base = {"status": "BLOCKED", "trade_ready": False, "notify": False,
            "automatic_orders": False, "order_placement_enabled": False,
            "research_only": True}
    if not isinstance(candidate, dict):
        return {**base, "blocks": ["CANDIDATE_INVALID"]}
    symbol = candidate.get("symbol")
    market = candidate.get("market", "US")
    if not isinstance(symbol, str) or not symbol.strip() or market != "US":
        return {**base, "blocks": ["IDENTITY_INVALID"]}
    if type(batch_index) is not int or not 0 <= batch_index < 21:
        return {**base, "blocks": ["BATCH_INVALID"]}
    observed, decision, last_bar = map(_parse, (source_observed_utc,
                                                decision_observed_utc,
                                                source_last_bar_utc))
    if None in (observed, decision, last_bar) or not last_bar <= observed <= decision:
        return {**base, "blocks": ["POINT_IN_TIME_PROVENANCE_INVALID"]}
    recovery = candidate.get("recovery_map")
    if not isinstance(recovery, dict):
        return {**base, "blocks": ["RECOVERY_MAP_MISSING"]}
    friction = recovery.get("first_friction_reference_usd")
    close = candidate.get("last_close_usd")
    if any(type(x) not in (int, float) or not 0 < x < float("inf")
           for x in (friction, close)):
        return {**base, "blocks": ["PRICE_OR_FRICTION_INVALID"]}
    if recovery.get("resistance_confirmed") is True:
        return {**base, "blocks": ["UNATTESTED_RESISTANCE_CLAIM"]}
    return {**base, "status": "WATCH_UNVERIFIED",
            "blocks": ["RESISTANCE_UNVERIFIED", "BROKER_QUOTE_UNVERIFIED",
                       "RISK_REWARD_UNVERIFIED", "EUR_NET_PROFIT_UNVERIFIED",
                       "FUTURE_BREAKOUT_NOT_OBSERVED"],
            "snapshot": {"symbol": symbol, "market": "US",
                         "batch_index": batch_index,
                         "source_observed_utc": source_observed_utc,
                         "source_last_bar_utc": source_last_bar_utc,
                         "decision_observed_utc": decision_observed_utc,
                         "historical_friction_usd": friction,
                         "historical_close_usd": close},
            "limitations": ["Caller-supplied timestamps are not independently attested",
                            "No subsequent observations or outcome inferred",
                            "Historical friction is not verified resistance"]}
