"""Conservative pre-alert daily context from *completed* prior UTC days.

A daily bar stamped on the notification date may be incomplete or include
post-notification trades, so it is excluded. Not a trade recommendation.
"""
from datetime import datetime, timezone

def pre_signal_metrics(signal_day, bars):
    if not isinstance(signal_day, str) or len(signal_day) != 10:
        raise ValueError("invalid_signal_day")
    rows=[]
    for b in bars:
        ts=b.get("timestamp")
        if not isinstance(ts,int):
            raise ValueError("invalid_timestamp")
        day=datetime.fromtimestamp(ts,timezone.utc).date().isoformat()
        if day >= signal_day:
            continue
        if any(not isinstance(b.get(k),(int,float)) or b[k] <= 0 for k in ("open","high","low","close")):
            raise ValueError("invalid_ohlc")
        if not b["low"] <= min(b["open"],b["close"]) <= max(b["open"],b["close"]) <= b["high"]:
            raise ValueError("inconsistent_ohlc")
        rows.append((day,b))
    dates=[day for day,_ in rows]
    if dates!=sorted(set(dates)):
        raise ValueError("unsorted_or_duplicate_days")
    if len(rows)<21:
        return {"status":"insufficient_history","prior_days":len(rows),"research_only":True}
    last=rows[-1][1]["close"]
    close_5=rows[-6][1]["close"]
    close_20=rows[-21][1]["close"]
    window=rows[-20:]
    low=min(b["low"] for _,b in window)
    high=max(b["high"] for _,b in window)
    return {
        "status":"historical_context_available",
        "prior_days":len(rows),
        "last_completed_day":rows[-1][0],
        "return_5_sessions_pct":round(100*(last/close_5-1),4),
        "return_20_sessions_pct":round(100*(last/close_20-1),4),
        "recovery_from_20_session_low_pct":round(100*(last/low-1),4),
        "distance_below_20_session_high_pct":round(100*(1-last/high),4),
        "signal_day_excluded":True,
        "research_only":True,
        "trade_ready":False,
    }
