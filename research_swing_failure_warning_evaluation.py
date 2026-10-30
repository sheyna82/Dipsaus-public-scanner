"""Historical, decision-dated warning evaluation; not a live alert.

A warning at close t is tested against future lows and closes, never used as
an intraday execution signal. Non-overlapping decisions are optional via step.
"""
from statistics import mean
from research_swing_failure_warning import failure_warning_at_close

def evaluate_failure_warnings(bars, *, horizon=5, step=5, drawdown_threshold_pct=-8):
    if horizon not in (5,10,15) or type(step) is not int or step<1:
        raise ValueError("invalid_window")
    observations=[]
    for symbol,rows in bars.items():
        for t in range(20,len(rows)-horizon,step):
            signal=failure_warning_at_close(rows,t)["warning"]
            entry=float(rows[t]["close"])
            future=rows[t+1:t+horizon+1]
            if entry<=0 or any(float(b["low"])<=0 or float(b["close"])<=0 for b in future):
                raise ValueError("invalid_future_price")
            future_min_pct=100*(min(b["low"] for b in future)/entry-1)
            forward_close_pct=100*(future[-1]["close"]/entry-1)
            event=future_min_pct<=drawdown_threshold_pct
            observations.append({"symbol":symbol,"decision_timestamp":rows[t]["timestamp"],
                                 "label_end_timestamp":rows[t+horizon]["timestamp"],
                                 "warning":signal,"future_large_drawdown":event,
                                 "future_min_pct":round(future_min_pct,4),
                                 "future_close_pct":round(forward_close_pct,4)})
    cutoff_by_symbol={s:sorted(x["decision_timestamp"] for x in observations if x["symbol"]==s)[int(0.7*(sum(x["symbol"]==s for x in observations)-1))] for s in bars if any(x["symbol"]==s for x in observations)}
    def segment_stats(segment):
        n=len(segment)
        tp_s=sum(x["warning"] and x["future_large_drawdown"] for x in segment)
        fp_s=sum(x["warning"] and not x["future_large_drawdown"] for x in segment)
        fn_s=sum(not x["warning"] and x["future_large_drawdown"] for x in segment)
        event_rate=(tp_s+fn_s)/n if n else None
        precision_s=tp_s/(tp_s+fp_s) if tp_s+fp_s else None
        return {"n":n,"warnings":tp_s+fp_s,"events":tp_s+fn_s,
                "precision":round(precision_s,4) if precision_s is not None else None,
                "base_rate":round(event_rate,4) if event_rate is not None else None,
                "lift":round(precision_s/event_rate,4) if precision_s is not None and event_rate else None}
    early=[x for x in observations if x["label_end_timestamp"]<=cutoff_by_symbol[x["symbol"]]]
    purged=sum(x["decision_timestamp"]<=cutoff_by_symbol[x["symbol"]] and x["label_end_timestamp"]>cutoff_by_symbol[x["symbol"]] for x in observations)
    late=[x for x in observations if x["decision_timestamp"]>cutoff_by_symbol[x["symbol"]]]
    tp=sum(x["warning"] and x["future_large_drawdown"] for x in observations)
    fp=sum(x["warning"] and not x["future_large_drawdown"] for x in observations)
    fn=sum(not x["warning"] and x["future_large_drawdown"] for x in observations)
    tn=sum(not x["warning"] and not x["future_large_drawdown"] for x in observations)
    base_rate=(tp+fn)/len(observations) if observations else None
    precision=tp/(tp+fp) if tp+fp else None
    return {"horizon":horizon,"threshold_pct":drawdown_threshold_pct,
            "event_base_rate":round(base_rate,4) if base_rate is not None else None,
            "precision_lift_vs_base_rate":round(precision/base_rate,4) if precision is not None and base_rate else None,
            "early_70pct":segment_stats(early),"late_30pct":segment_stats(late),
            "purged_boundary_observations":purged,
            "observations":len(observations),"tp":tp,"fp":fp,"fn":fn,"tn":tn,
            "precision":round(tp/(tp+fp),4) if tp+fp else None,
            "recall":round(tp/(tp+fn),4) if tp+fn else None,
            "warning_rate":round((tp+fp)/len(observations),4) if observations else None,
            "mean_forward_close_warning_pct":round(mean(x["future_close_pct"] for x in observations if x["warning"]),4) if tp+fp else None,
            "mean_forward_close_no_warning_pct":round(mean(x["future_close_pct"] for x in observations if not x["warning"]),4) if fn+tn else None,
            "event_calendar_verified":False,"research_only":True,
            "trade_ready":False,"edge_proven":False}
