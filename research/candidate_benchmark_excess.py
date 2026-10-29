"""Predeclared benchmark-relative sensitivity, research only; not a causal control."""
import json, statistics
from datetime import datetime, timezone
from pathlib import Path
from candidate_entry_snapshot import bars
from candidate_regime_cost_validation import RESEARCH_UNIVERSE, features, nonoverlap, MIN_TRAIN

BENCHMARKS={"US":"SPY","EU":"VGK"}
HORIZON=10
COST_BPS=50
PATTERNS=("breakout_prior20","recovery_from_prior20_low_3to15pct")

def market(symbol):
    return "US" if "." not in symbol else "EU"

def compare(stock, benchmark, pattern):
    cutoff=max(MIN_TRAIN,int(len(stock)*.65))
    benchmark_by_date={datetime.fromtimestamp(r["timestamp"],timezone.utc).date():r
                       for r in benchmark}
    indices=nonoverlap([i for i in range(cutoff,len(stock)-HORIZON)
                        if features(stock,i)[pattern]],HORIZON)
    differences=[]
    missing=0
    for i in indices:
        entry=datetime.fromtimestamp(stock[i+1]["timestamp"],timezone.utc).date()
        exit_day=datetime.fromtimestamp(stock[i+HORIZON]["timestamp"],timezone.utc).date()
        start,end=benchmark_by_date.get(entry),benchmark_by_date.get(exit_day)
        if not start or not end or start["open"]<=0:
            missing+=1
            continue
        stock_pct=100*(stock[i+HORIZON]["close"]/stock[i+1]["open"]-1)-COST_BPS/100
        benchmark_pct=100*(end["close"]/start["open"]-1)
        differences.append(stock_pct-benchmark_pct)
    if missing or not differences:
        return {"status":"BLOCKED_BENCHMARK_ALIGNMENT" if missing else "NO_SIGNALS",
                "signal_n":len(indices),"aligned_n":len(differences),
                "missing_alignment_n":missing,"trade_ready":False}
    return {"status":"DESCRIPTIVE_ONLY","signal_n":len(indices),
            "aligned_n":len(differences),"missing_alignment_n":0,
            "median_excess_pct":round(statistics.median(differences),3),
            "positive_excess_fraction":round(sum(x>0 for x in differences)/len(differences),3),
            "trade_ready":False}

def main():
    output={"research_only":True,"trade_ready":False,
            "method":"NEXT_OPEN_TO_HORIZON_CLOSE_BENCHMARK_EXCESS",
            "horizon_sessions":HORIZON,"stock_roundtrip_cost_bps":COST_BPS,
            "benchmarks":BENCHMARKS,
            "limitations":["SPY and VGK are broad proxies, not sector-matched controls",
                           "Yahoo daily unadjusted bars; corporate actions and currency unverified",
                           "Overlapping cross-symbol events are correlated",
                           "No benchmark trade costs deducted; descriptive, not causal",
                           "Historical universe is not survivorship-free"],
            "candidates":[]}
    bench={}
    for key,symbol in BENCHMARKS.items():
        try:bench[key]=bars(symbol,history_range="5y")
        except Exception:bench[key]=None
    for symbol in RESEARCH_UNIVERSE:
        key=market(symbol)
        try:
            if not bench[key]:raise ValueError("BENCHMARK_DATA_UNAVAILABLE")
            stock=bars(symbol,history_range="5y")
            if len(stock)<750:raise ValueError("INSUFFICIENT_STOCK_HISTORY")
            output["candidates"].append({"symbol":symbol,"benchmark":BENCHMARKS[key],
                "patterns":{p:compare(stock,bench[key],p) for p in PATTERNS}})
        except Exception as exc:
            output["candidates"].append({"symbol":symbol,"status":"DATA_BLOCKED",
                                         "error_type":type(exc).__name__})
    dest=Path("reports/candidate_benchmark_excess.json")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps({"status":"RESEARCH_ONLY","candidates":len(output["candidates"])}))

if __name__=="__main__":main()
