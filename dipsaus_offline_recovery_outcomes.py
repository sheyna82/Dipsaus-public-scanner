"""Offline first-touch recovery outcomes for daily OHLC, without trade simulation.

The first bar is the signal-day CLOSE; later bars must be future sessions.
Caller must provide split-consistent prices and independently verified dates.
"""
import math
from datetime import date


def evaluate_recovery_path(bars, gain_pct=3.0, loss_pct=5.0, horizon=10):
    if (not isinstance(bars, (list, tuple)) or type(horizon) is not int
            or horizon < 1 or type(gain_pct) not in (int, float)
            or type(loss_pct) not in (int, float)
            or not math.isfinite(gain_pct) or not math.isfinite(loss_pct)
            or gain_pct <= 0 or loss_pct <= 0):
        return None
    dates = []
    for bar in bars:
        if not isinstance(bar, dict):
            return None
        try:
            d = date.fromisoformat(bar["date"])
            if d.isoformat() != bar["date"]:
                return None
        except (KeyError, TypeError, ValueError):
            return None
        vals = [bar.get(k) for k in ("high", "low", "close")]
        if (any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                for v in vals) or not (vals[1] <= vals[2] <= vals[0])):
            return None
        dates.append(d)
    if len(set(dates)) != len(dates) or dates != sorted(dates) or not bars:
        return None
    entry = bars[0]["close"]
    future = bars[1:horizon + 1]
    if len(future) < horizon:
        return {"status": "INSUFFICIENT_FUTURE_DATA", "research_only": True,
                "trade_ready": False, "order_instruction": None}
    gain_price = entry * (1 + gain_pct / 100)
    loss_price = entry * (1 - loss_pct / 100)
    first = "TIMEOUT"
    touch_session = None
    for i, bar in enumerate(future, start=1):
        gain = bar["high"] >= gain_price
        loss = bar["low"] <= loss_price
        if gain and loss:
            first, touch_session = "AMBIGUOUS_SAME_BAR", i
            break
        if gain or loss:
            first, touch_session = ("GAIN_FIRST" if gain else "LOSS_FIRST"), i
            break
    max_gain = max(100 * (b["high"] / entry - 1) for b in future)
    max_loss = min(100 * (b["low"] / entry - 1) for b in future)
    return {"status": first, "touch_session": touch_session,
            "close_return_pct": round(100 * (future[-1]["close"] / entry - 1), 4),
            "max_favorable_pct": round(max_gain, 4),
            "max_adverse_pct": round(max_loss, 4),
            "horizon_sessions": horizon, "gain_threshold_pct": gain_pct,
            "loss_threshold_pct": loss_pct, "research_only": True,
            "trade_ready": False, "order_instruction": None,
            "limitations": "OHLC cannot resolve intraday touch order; no execution or fees modeled."}
