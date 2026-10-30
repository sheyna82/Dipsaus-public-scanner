"""Pre-signal daily price context, not a retrospective entry recommendation."""
from datetime import datetime, timezone

def pre_signal_context(signal_utc, bars, lookback=20):
    if not isinstance(signal_utc, datetime) or signal_utc.tzinfo is None:
        raise ValueError("utc_aware_signal_required")
    if signal_utc.utcoffset().total_seconds() != 0:
        raise ValueError("timestamp_must_be_utc")
    if not isinstance(lookback, int) or lookback < 2:
        raise ValueError("invalid_lookback")
    cutoff = int(signal_utc.timestamp())
    prior = [b for b in bars if isinstance(b.get("timestamp"), int)
             and b["timestamp"] < cutoff]
    prior.sort(key=lambda b: b["timestamp"])
    prior = prior[-lookback:]
    if len(prior) < lookback:
        return None
    for b in prior:
        if any(not isinstance(b.get(k), (int, float)) or b[k] <= 0
               for k in ("open", "high", "low", "close")):
            raise ValueError("invalid_price_bar")
    current = prior[-1]["close"]
    bottom = min(b["low"] for b in prior)
    top = max(b["high"] for b in prior)
    return {
        "observed_bars": len(prior),
        "last_bar_timestamp": prior[-1]["timestamp"],
        "last_close": current,
        "lookback_low": bottom,
        "lookback_high": top,
        "recovery_from_low_pct": round((current / bottom - 1) * 100, 4),
        "distance_below_high_pct": round((1 - current / top) * 100, 4),
        "intraday_at_signal_known": False,
        "research_only": True,
    }
