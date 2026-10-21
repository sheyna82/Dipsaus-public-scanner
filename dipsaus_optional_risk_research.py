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
