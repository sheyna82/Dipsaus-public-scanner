"""Descriptive EXE risk context; no threshold tuning or live alerts.

Report the largest observed peak-to-close decline inside each complete span
so an absent 2% trigger is interpreted with actual price magnitude.
"""
from math import isfinite


def summarize_span_drawdown(bars):
    if not bars:
        return {"status": "INSUFFICIENT_DATA", "trade_ready": False}
    try:
        peak = 0.
        worst = 0.
        worst_index = None
        for i, bar in enumerate(bars):
            hi = float(bar["high"])
            close = float(bar["close"])
            lo = float(bar["low"])
            op = float(bar["open"])
            if not all(isfinite(v) and v > 0 for v in (hi, close, lo, op)):
                raise ValueError("nonfinite")
            if not lo <= min(op, close) <= max(op, close) <= hi:
                raise ValueError("invalid_ohlc")
            peak = max(peak, hi)
            drawdown = (close/peak-1)*100
            if drawdown < worst:
                worst, worst_index = drawdown, i
        return {"status": "DESCRIPTIVE_ONLY",
                "worst_peak_to_close_pct": round(worst, 4),
                "worst_index": worst_index, "trade_ready": False}
    except (ValueError, TypeError, KeyError, OverflowError):
        return {"status": "DATA_BLOCKED", "trade_ready": False}
