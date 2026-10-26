"""Research-only next-session-open swing exit policy A/B.

All decisions use completed daily closes; executions use the following open.
No intraday target fills, stop orders, earnings knowledge, or portfolio claims.
"""
from math import isfinite
from statistics import mean
from research_swing_failure_warning import failure_warning_at_close

def simulate_exit_policies(rows, decision_index, horizon, *, round_trip_cost_bps=30):
    if horizon not in (5,10,15) or type(decision_index) is not int or decision_index<20:
        raise ValueError("invalid_window")
    if decision_index+horizon>=len(rows) or not 0<=round_trip_cost_bps<=1000:
        raise ValueError("invalid_assumptions")
    end=decision_index+horizon
    for bar in rows[decision_index-20:end+1]:
        for key in ("open","high","low","close"):
            value=bar[key]
            if not isinstance(value,(int,float)) or not isfinite(value) or value<=0:
                raise ValueError("invalid_price")
        if bar["low"]>min(bar["open"],bar["close"]) or bar["high"]<max(bar["open"],bar["close"]):
            raise ValueError("inconsistent_bar")
    entry=rows[decision_index+1]["open"]
    def net(fills):
        return round(sum(weight*(100*(price/entry-1)-round_trip_cost_bps/100)
                         for weight,price in fills),5)
    baseline=net([(1,rows[end]["close"])])
    # First qualifying close can only trigger an exit at the NEXT open.
    warning_exit=None
    profit_exit=None
    for t in range(decision_index+1,end):
        if warning_exit is None and failure_warning_at_close(rows,t)["warning"]:
            warning_exit=t+1
        if profit_exit is None and rows[t]["close"]/entry-1>=.05:
            profit_exit=t+1
    warning_net=net([(1,rows[warning_exit]["open"])]) if warning_exit is not None else baseline
    # Half is realized after a +5% decision close; remainder follows warning or time.
    first=profit_exit
    if first is None:
        partial_net=warning_net
    else:
        remaining_exit=next((t+1 for t in range(first,end)
                             if failure_warning_at_close(rows,t)["warning"]),None)
        remainder_price=rows[remaining_exit]["open"] if remaining_exit else rows[end]["close"]
        partial_net=net([(.5,rows[first]["open"]),(.5,remainder_price)])
    return {"baseline_net_pct":baseline,"warning_exit_net_pct":warning_net,
            "partial_profit_net_pct":partial_net,
            "warning_exit_index":warning_exit,"partial_profit_exit_index":profit_exit,
            "entry_index":decision_index+1,"planned_exit_index":end,
            "execution_model":"next_open_after_close_signal",
            "round_trip_cost_bps":round_trip_cost_bps,
            "research_only":True,"trade_ready":False}

def compare_exit_policies(bars, *, horizon=10, step=15, round_trip_cost_bps=30):
    if type(step) is not int or step<horizon:
        raise ValueError("overlapping_cohorts_not_supported")
    observations=[]
    for symbol,rows in bars.items():
        for t in range(20,len(rows)-horizon,step):
            record=simulate_exit_policies(rows,t,horizon,round_trip_cost_bps=round_trip_cost_bps)
            record.update(symbol=symbol,decision_timestamp=rows[t]["timestamp"])
            observations.append(record)
    names=("baseline","warning_exit","partial_profit")
    cutoffs={s:sorted(x["decision_timestamp"] for x in observations if x["symbol"]==s)[int(.7*(sum(x["symbol"]==s for x in observations)-1))] for s in bars if any(x["symbol"]==s for x in observations)}
    early=[x for x in observations if x["decision_timestamp"]<=cutoffs[x["symbol"]]]
    late=[x for x in observations if x["decision_timestamp"]>cutoffs[x["symbol"]]]
    def period_mean(items,name):
        return round(mean(x[name+"_net_pct"] for x in items),4) if items else None
    return {"horizon":horizon,"observations":len(observations),
            "early_observations":len(early),"late_observations":len(late),
            "policies":{name:{"mean_net_pct":round(mean(x[name+"_net_pct"] for x in observations),4) if observations else None,
                              "negative_outcomes":sum(x[name+"_net_pct"]<0 for x in observations),
                              "early_mean_net_pct":period_mean(early,name),
                              "late_mean_net_pct":period_mean(late,name),
                              "worst_net_pct":round(min(x[name+"_net_pct"] for x in observations),4) if observations else None}
                        for name in names},
            "warning_exits":sum(x["warning_exit_index"] is not None for x in observations),
            "partial_profit_exits":sum(x["partial_profit_exit_index"] is not None for x in observations),
            "research_only":True,"trade_ready":False,"portfolio_overlap_modelled":False,
            "edge_proven":False}
