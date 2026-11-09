"""Research-only European relative strength with explicit benchmark provenance gate."""
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import math

PAIRS={"ASML.AS":"AEX","IFX.DE":"DAX_PRICE","NOKIA.HE":"OMXH25","RHM.DE":"DAX_PRICE"}
def session_day(bar,zone):
    return datetime.fromtimestamp(bar["t"],timezone.utc).astimezone(ZoneInfo(zone)).date().isoformat()
ZONES={"ASML.AS":"Europe/Amsterdam","IFX.DE":"Europe/Berlin","NOKIA.HE":"Europe/Helsinki","RHM.DE":"Europe/Berlin"}
BENCH_ZONES={"AEX":"Europe/Amsterdam","DAX_PRICE":"Europe/Berlin","OMXH25":"Europe/Helsinki","STOXX600_PRICE":"Europe/Paris"}
def compare(europe,benchmarks,identity_evidence,as_of_complete_day):
    # Explicitly supplied and frozen by caller; never silently assume a date.
    from datetime import date
    try:
        cutoff=date.fromisoformat(as_of_complete_day)
        if cutoff.isoformat()!=as_of_complete_day:raise ValueError()
    except (TypeError,ValueError):
        raise ValueError('INVALID_COMPLETE_SESSION_CUTOFF')
    if europe.get("trade_ready") is not False or benchmarks.get("trade_ready") is not False:
        raise ValueError("RESEARCH_ONLY_REQUIRED")
    if not identity_evidence or set(identity_evidence)!={"AEX","DAX_PRICE","OMXH25","STOXX600_PRICE"} or not all(identity_evidence.values()):
        raise ValueError("BENCHMARK_IDENTITY_UNVERIFIED")
    result={}
    for stock,primary in PAIRS.items():
        stock_bars=europe["series"][stock]["bars"]
        stock_by_date={session_day(b,ZONES[stock]):b for b in stock_bars}
        if len(stock_by_date)!=len(stock_bars):raise ValueError("DUPLICATE_STOCK_SESSION")
        result[stock]={}
        for name in (primary,"STOXX600_PRICE"):
            index_bars=benchmarks["series"][name]["bars"]
            idx={session_day(b,BENCH_ZONES[name]):b for b in index_bars}
            if len(idx)!=len(index_bars):raise ValueError("DUPLICATE_BENCHMARK_SESSION")
            common=sorted(set(stock_by_date)&set(idx))
            # Never use current, potentially incomplete session. Explicitly choose
            # a fixed last complete day in the caller's research protocol.
            common=[d for d in common if d<=as_of_complete_day]
            if len(common)<21:raise ValueError("INSUFFICIENT_MATCHED_DAYS")
            last,prior=common[-1],common[-21]
            a=stock_by_date[last]["close"]/stock_by_date[prior]["close"]-1
            b=idx[last]["close"]/idx[prior]["close"]-1
            rs=100*(a-b)
            if not math.isfinite(rs):raise ValueError("NONFINITE")
            result[stock][name]={"last_complete_day":last,"prior_day":prior,"relative_strength_20d_pct":rs,
                                  "matched_sessions":len(common),"trade_ready":False}
    return {"schema":"dipsaus_eu_relative_strength_research_v1","research_only":True,"trade_ready":False,
            "selection_thresholds_approved":False,"comparisons":result}
