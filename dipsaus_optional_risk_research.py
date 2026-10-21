"""Offline, advisory-only technical risk context; never place orders or notify.

ATR and recent support are observations, not guaranteed loss limits or stop prices.
"""
import math


def _positive(x):
    return type(x) in (int, float) and math.isfinite(x) and x > 0


def assess_risk(bars, entry_price, lookback=14, support_window=10,
                optional_stop_advice=False):
    """Compute ATR, recent support and downside distance from chronological OHLC.

    Optional stop advice is intentionally NOT implemented or enabled: toggling
    it requires a separately reviewed design and explicit user authorization.
    """
    if optional_stop_advice is not False:
        return None
    if (not isinstance(bars, (list, tuple)) or len(bars) < max(lookback + 1, support_window)
            or not _positive(entry_price) or type(lookback) is not int or lookback < 2
            or type(support_window) is not int or support_window < 2):
        return None
    for bar in bars:
        if (not isinstance(bar, dict) or any(not _positive(bar.get(k))
                for k in ("high", "low", "close"))
                or bar["low"] > bar["close"] or bar["high"] < bar["close"]):
            return None
    ranges = []
    for i in range(len(bars) - lookback, len(bars)):
        current, prior = bars[i], bars[i - 1]
        ranges.append(max(current["high"] - current["low"],
                          abs(current["high"] - prior["close"]),
                          abs(current["low"] - prior["close"])))
    atr = sum(ranges) / lookback
    support = min(bar["low"] for bar in bars[-support_window:])
    return {
        "atr": round(atr, 4),
        "atr_pct_of_entry": round(100 * atr / entry_price, 4),
        "recent_support": round(support, 4),
        "distance_to_support_pct": round(100 * (support / entry_price - 1), 4),
        "support_already_breached": entry_price < support,
        "risk_reference_only": True,
        "stop_advice_enabled": False,
        "stop_order_created": False,
        "trade_ready": False,
        "notify": False,
        "note": "Historical structure only; gaps can cause losses beyond support. No execution guarantee.",
    }


def assess_structure_pressure(risk_context, observed_price):
    """Describe pressure relative to historical support and ATR, not a sell signal.

    Below-support observations need independent confirmation. ATR is a volatility
    scale, not a guarantee, and this is not a trailing stop.
    """
    if (not isinstance(risk_context, dict) or risk_context.get("risk_reference_only") is not True
            or not _positive(observed_price)
            or not _positive(risk_context.get("recent_support"))
            or not _positive(risk_context.get("atr"))):
        return None
    support = risk_context["recent_support"]
    atr = risk_context["atr"]
    distance_atr = (observed_price - support) / atr
    if observed_price >= support:
        state = "ABOVE_REFERENCE_SUPPORT"
    elif distance_atr >= -0.5:
        state = "BELOW_SUPPORT_REVIEW"
    else:
        state = "DEEPER_SUPPORT_BREACH_REVIEW"
    return {
        "state": state,
        "distance_from_support_atr": round(distance_atr, 4),
        "independent_confirmation_required": state != "ABOVE_REFERENCE_SUPPORT",
        "research_only": True,
        "trade_ready": False,
        "sell_recommendation": False,
        "stop_advice_enabled": False,
        "notify": False,
        "note": "One observed price cannot confirm a trend break; validate timing, market and fresh price.",
    }
