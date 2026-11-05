"""Research-only intratrade adverse/favorable excursion for dated swing cohorts.

Daily OHLC bars measure observed low/high after next-session open, through
the exit session. These are NOT executable fills or intraday event ordering.
"""
from math import isfinite

def excursion_for_trade(rows, decision_index, horizon, *, entry_cost_bps=0):
    if type(decision_index) is not int or type(horizon) is not int or horizon not in (5,10,15):
        raise ValueError("invalid_trade_indices")
    if decision_index < 0 or decision_index + horizon >= len(rows):
        raise ValueError("insufficient_future_bars")
    entry = rows[decision_index+1]["open"]
    if not isfinite(entry) or entry <= 0:
        raise ValueError("invalid_entry")
    window = rows[decision_index+1:decision_index+horizon+1]
    for bar in window:
        if any(not isinstance(bar[k], (int,float)) or not isfinite(bar[k]) or bar[k] <= 0 for k in ("high","low","close")):
            raise ValueError("invalid_bar")
        if bar["low"] > bar["high"]:
            raise ValueError("inverted_bar")
    mae = 100*(min(bar["low"] for bar in window)/entry-1)
    mfe = 100*(max(bar["high"] for bar in window)/entry-1)
    exit_return = 100*(window[-1]["close"]/entry-1)-entry_cost_bps/100
    return {"mae_pct":round(mae,5),"mfe_pct":round(mfe,5),
            "exit_net_pct":round(exit_return,5),
            "intra_session_order_known":False,
            "research_only":True}

def summarize_excursions(observations):
    if not observations:
        raise ValueError("empty_observations")
    from statistics import mean,median
    return {"trades":len(observations),
            "mean_mae_pct":round(mean(x["mae_pct"] for x in observations),4),
            "worst_mae_pct":round(min(x["mae_pct"] for x in observations),4),
            "median_mae_pct":round(median(x["mae_pct"] for x in observations),4),
            "mean_mfe_pct":round(mean(x["mfe_pct"] for x in observations),4),
            "share_mae_below_minus_10pct":round(sum(x["mae_pct"]<=-10 for x in observations)/len(observations),4)}
