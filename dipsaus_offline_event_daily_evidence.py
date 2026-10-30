"""Research-only observed daily price evidence, not a predictive model.

Caller supplies an independently verified market session and data provenance.
Daily bars cannot establish intraday support, executable spreads or fills.
"""
from dipsaus_offline_ohlcv_csv import load_local_ohlcv_csv


def derive_daily_event_evidence(path, *, expected_session, source_verified=False):
    if source_verified is not True:
        return {"status": "DATA_BLOCKED", "reason": "source_unverified"}
    bars = load_local_ohlcv_csv(path)
    if bars is None or len(bars) < 22:
        return {"status": "DATA_BLOCKED", "reason": "invalid_history"}
    if not isinstance(expected_session, str) or bars[-1]["date"] != expected_session:
        return {"status": "DATA_BLOCKED", "reason": "session_not_verified"}
    # This is a deliberately simple, predeclared technical observation:
    # two successive rising closes and latest close above prior 5-day mean.
    last = bars[-1]
    trend = (bars[-3]["close"] < bars[-2]["close"] < last["close"]
             and last["close"] > sum(b["close"] for b in bars[-6:-1]) / 5)
    # Caution if close falls >3% versus prior close, or latest range >2x
    # prior 14-session mean daily range. Neither represents a stop order.
    prior = bars[-2]["close"]
    mean_range = sum(b["high"] - b["low"] for b in bars[-15:-1]) / 14
    risk = (last["close"] / prior - 1 <= -0.03 or
            last["high"] - last["low"] > 2 * mean_range)
    return {"status": "OBSERVED_DAILY_ONLY", "quote_fresh": True,
            "trend_confirmed": trend, "downside_warning": risk,
            "observed_session": expected_session, "source_verified": True,
            "limitations": "Caller-verified daily session; descriptive rules only, not intraday confirmation or forecast."}
