"""Research-only dated failure-warning indicators, evaluated at decision close.

Signals are descriptive, not an executable exit instruction. No claim of
earnings/calendar coverage, predictive calibration or intraday fill ordering.
"""
from math import isfinite
from statistics import mean

def failure_warning_at_close(rows, t, *, lookback=20):
    if type(t) is not int or t < lookback or t >= len(rows):
        raise ValueError("insufficient_history")
    window=rows[t-lookback:t+1]
    for bar in window:
        for k in ("open","high","low","close"):
            if k not in bar or not isinstance(bar[k],(int,float)) or not isfinite(bar[k]) or bar[k]<=0:
                raise ValueError("invalid_ohlc")
        if not bar["low"]<=bar["open"]<=bar["high"] or not bar["low"]<=bar["close"]<=bar["high"]:
            raise ValueError("inconsistent_ohlc")
    today=window[-1]
    prev=window[-2]
    gap_pct=100*(today["open"]/prev["close"]-1)
    close_location=(today["close"]-today["low"])/(today["high"]-today["low"]) if today["high"]>today["low"] else 0.5
    prior_low=min(b["low"] for b in window[:-1])
    breakdown=today["close"]<prior_low
    failed_recovery=today["close"]<mean(b["close"] for b in window[-10:]) and today["close"]<prev["close"]
    warning=(gap_pct<=-5 or (breakdown and close_location<=0.25) or
             (failed_recovery and close_location<=0.15))
    return {"warning":warning,"gap_pct":round(gap_pct,4),
            "close_location":round(close_location,4),
            "breakdown":breakdown,"failed_recovery":failed_recovery,
            "event_calendar_verified":False,"volume_confirmed":False,
            "thresholds_validated_out_of_sample":False,
            "research_only":True}
