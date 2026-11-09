"""Research-only consecutive-session recovery confirmation; no buy decisions."""
from datetime import date
import math

def evaluate(history, as_of_complete_day, benchmark_identity_verified=False):
    if benchmark_identity_verified is not True:
        raise ValueError("BENCHMARK_IDENTITY_UNVERIFIED")
    try:
        cutoff=date.fromisoformat(as_of_complete_day)
        if cutoff.isoformat()!=as_of_complete_day: raise ValueError()
    except (TypeError,ValueError):
        raise ValueError("INVALID_COMPLETE_DAY")
    if not isinstance(history,list): raise ValueError("INVALID_HISTORY")
    eligible=[]
    seen=set()
    for item in history:
        day=item.get("day")
        try: d=date.fromisoformat(day)
        except (TypeError,ValueError): raise ValueError("INVALID_DAY")
        if day in seen:raise ValueError("DUPLICATE_DAY")
        seen.add(day)
        if d>cutoff:continue  # excludes partial and future bars
        a=item.get("stock_close")
        b=item.get("benchmark_close")
        for v in (a,b):
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0:
                raise ValueError("INVALID_CLOSE")
        eligible.append((day,float(a),float(b)))
    eligible.sort()
    if len(eligible)<3:raise ValueError("INSUFFICIENT_COMPLETED_SESSIONS")
    # Two consecutive relative one-session gains; no implicit threshold approval.
    daily=[]
    for previous,current in zip(eligible[-3:],eligible[-2:]):
        stock=100*(current[1]/previous[1]-1)
        bench=100*(current[2]/previous[2]-1)
        daily.append({"day":current[0],"relative_change_pp":stock-bench})
    confirmed=all(x["relative_change_pp"]>0 for x in daily)
    return {"schema":"dipsaus_eu_recovery_observation_v1","research_only":True,
            "trade_ready":False,"approved_signal":False,
            "two_positive_relative_sessions":confirmed,
            "latest_complete_day":eligible[-1][0],"observations":daily}
