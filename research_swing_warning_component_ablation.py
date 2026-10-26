"""Research-only ablation of warning components; no trading instructions.

All signals are computed using information available at decision close.
"""
from statistics import mean
from research_swing_failure_warning import failure_warning_at_close

SIGNALS = ("gap", "breakdown_weak_close", "failed_recovery_weak_close", "combined")

def evaluate_warning_components(bars, *, horizon=10, step=5, drawdown_threshold_pct=-8):
    if horizon not in (5, 10, 15) or type(step) is not int or step < 1:
        raise ValueError("invalid_window")
    records = []
    for symbol, rows in bars.items():
        for t in range(20, len(rows)-horizon, step):
            info = failure_warning_at_close(rows, t)
            signals = {
                "gap": info["gap_pct"] <= -5,
                "breakdown_weak_close": info["breakdown"] and info["close_location"] <= .25,
                "failed_recovery_weak_close": info["failed_recovery"] and info["close_location"] <= .15,
                "combined": info["warning"],
            }
            entry = float(rows[t]["close"])
            if entry <= 0:
                raise ValueError("invalid_entry")
            future = rows[t+1:t+horizon+1]
            if any(float(b["low"]) <= 0 or float(b["close"]) <= 0 for b in future):
                raise ValueError("invalid_future_price")
            minimum = 100*(min(float(b["low"]) for b in future)/entry-1)
            close_return = 100*(float(future[-1]["close"])/entry-1)
            records.append(dict(symbol=symbol, decision=rows[t]["timestamp"],
                                label_end=rows[t+horizon]["timestamp"],
                                event=minimum <= drawdown_threshold_pct,
                                forward_close_pct=close_return, signals=signals))
    def metrics(items, signal):
        n = len(items)
        tp = sum(x["signals"][signal] and x["event"] for x in items)
        fp = sum(x["signals"][signal] and not x["event"] for x in items)
        fn = sum(not x["signals"][signal] and x["event"] for x in items)
        precision = tp/(tp+fp) if tp+fp else None
        base = (tp+fn)/n if n else None
        returns = [x["forward_close_pct"] for x in items if x["signals"][signal]]
        return dict(n=n, tp=tp, fp=fp, fn=fn,
                    precision=round(precision, 4) if precision is not None else None,
                    recall=round(tp/(tp+fn), 4) if tp+fn else None,
                    base_rate=round(base, 4) if base is not None else None,
                    lift=round(precision/base, 4) if precision is not None and base else None,
                    mean_forward_close_warning_pct=round(mean(returns), 4) if returns else None)
    cutoffs = {}
    for symbol in bars:
        dates = sorted(x["decision"] for x in records if x["symbol"] == symbol)
        if dates:
            cutoffs[symbol] = dates[int(.7*(len(dates)-1))]
    early = [x for x in records if x["label_end"] <= cutoffs[x["symbol"]]]
    late = [x for x in records if x["decision"] > cutoffs[x["symbol"]]]
    return dict(horizon=horizon, observations=len(records),
                purged_boundary_observations=len(records)-len(early)-len(late),
                components={name:dict(all=metrics(records,name),
                                      early=metrics(early,name),
                                      late=metrics(late,name)) for name in SIGNALS},
                research_only=True, trade_ready=False, edge_proven=False)
