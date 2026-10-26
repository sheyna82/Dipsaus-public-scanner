"""Research-only single-name downside screen and risk-scaled allocation.

All features end at the decision close. No earnings calendar is available:
event-risk coverage remains explicitly unknown, never treated as cleared.
"""
from math import isfinite
from statistics import mean, pstdev

def individual_risk_at_close(rows, t, *, lookback=20):
    if t < lookback or t >= len(rows):
        raise ValueError("insufficient_history")
    window=rows[t-lookback:t+1]
    closes=[float(x["close"]) for x in window]
    if any(not isfinite(x) or x<=0 for x in closes):
        raise ValueError("invalid_close")
    returns=[closes[i]/closes[i-1]-1 for i in range(1,len(closes))]
    daily_vol_pct=100*pstdev(returns)
    worst_day_pct=100*min(returns)
    gap_pct=100*min(float(window[i]["open"])/closes[i-1]-1 for i in range(1,len(window)))
    if not all(isfinite(float(x["open"])) and float(x["open"])>0 for x in window):
        raise ValueError("invalid_open")
    # Pre-registered candidate thresholds, NOT fitted/validated.
    extreme=daily_vol_pct>=5 or worst_day_pct<=-10 or gap_pct<=-8
    elevated=daily_vol_pct>=3 or worst_day_pct<=-6 or gap_pct<=-5
    return {"daily_vol_pct":round(daily_vol_pct,4),
            "worst_daily_return_pct":round(worst_day_pct,4),
            "worst_overnight_gap_pct":round(gap_pct,4),
            "risk_band":"extreme" if extreme else "elevated" if elevated else "ordinary",
            "event_calendar_verified":False,"liquidity_verified":False,
            "thresholds_validated_out_of_sample":False}

def allocation_fraction(risk, variant):
    if variant=="baseline":
        return 1.0
    if variant not in ("screen","scaled"):
        raise ValueError("unknown_variant")
    if risk["risk_band"]=="extreme":
        return 0.0
    if variant=="screen":
        return 1.0
    return 0.5 if risk["risk_band"]=="elevated" else 1.0
