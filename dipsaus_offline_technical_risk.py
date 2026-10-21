"""Pure offline technical risk research. No orders, alerts, or network access."""
import math

def _valid(x):
    return type(x) in (int, float) and math.isfinite(x) and x > 0

def assess_risk(bars, entry, target=None, period=14, stoploss_advice=False):
    """Chronological OHLC dictionaries. Outputs research references, never orders."""
    if stoploss_advice is not False or type(period) is not int or period < 2:
        return None
    if not isinstance(bars, (list, tuple)) or len(bars) < period + 1 or not _valid(entry):
        return None
    if target is not None and not _valid(target):
        return None
    for b in bars:
        if not isinstance(b, dict) or any(not _valid(b.get(k)) for k in ("high", "low", "close")):
            return None
        if b["low"] > b["close"] or b["close"] > b["high"]:
            return None
    trs = []
    for previous, current in zip(bars, bars[1:]):
        trs.append(max(current["high"] - current["low"],
                       abs(current["high"] - previous["close"]),
                       abs(current["low"] - previous["close"])))
    atr = sum(trs[-period:]) / period
    previous_atr = (sum(trs[-2*period:-period]) / period
                    if len(trs) >= 2 * period else None)
    volatility_expansion = (atr / previous_atr >= 1.5
                            if previous_atr is not None and previous_atr > 0 else None)
    previous_low = min(b["low"] for b in bars[-11:-1])
    trend_break = bars[-1]["close"] < previous_low
    invalidation = min(b["low"] for b in bars[-10:])
    downside = entry - invalidation
    upside = target - entry if target is not None else None
    rr = upside / downside if upside is not None and upside > 0 and downside > 0 else None
    return {"atr": round(atr, 6), "atr_pct_of_entry": round(100 * atr / entry, 4),
            "technical_invalidation_reference": invalidation,
            "volatility_expansion_1_5x": volatility_expansion,
            "trend_break_below_previous_10_bar_low": trend_break,
            "risk_reward": round(rr, 4) if rr is not None else None,
            "risk_reward_unresolved": rr is None,
            "invalidation_below_entry": downside > 0,
            "stoploss_advice_enabled": False, "order_instruction": None,
            "research_only": True, "trade_ready": False,
            "warning": "Invalidation is not a guaranteed exit price or maximum loss."}
