"""Benchmark-matched post-earnings outcomes, research-only.

A benchmark bar must exist on the EXACT stock entry and exit dates.
No nearest-date substitution, no unverified trading claims.
"""
import argparse,collections,json,math,statistics
from pathlib import Path

def compare(outcomes,benchmark_bars,cost_bps=20):
    if not 0<=cost_bps<=1000: raise ValueError("invalid_cost_bps")
    benchmark={}
    for bar in benchmark_bars:
        day=bar["date"]
        if day in benchmark: raise ValueError("duplicate_benchmark_date")
        op,cl=float(bar["open"]),float(bar["close"])
        if not all(math.isfinite(x) and x>0 for x in (op,cl)): raise ValueError("invalid_benchmark_price")
        benchmark[day]=(op,cl)
    seen=set(); rows=[]; missing=collections.Counter()
    for r in outcomes:
        key=(r["symbol"],r["event_date"],r["horizon"])
        if key in seen: raise ValueError("duplicate_event_horizon")
        seen.add(key)
        if not r["event_date"]<r["entry_date"]<=r["exit_date"]: raise ValueError("invalid_event_chronology")
        if r["entry_date"] not in benchmark or r["exit_date"] not in benchmark:
            missing[r["horizon"]]+=1;continue
        stock=float(r["gross_return_pct"])
        if not math.isfinite(stock): raise ValueError("invalid_stock_return")
        bench=100*(benchmark[r["exit_date"]][1]/benchmark[r["entry_date"]][0]-1)
        # Both legs pay same assumed round-trip costs; costs cancel in excess return.
        rows.append({"symbol":r["symbol"],"event_date":r["event_date"],
            "entry_date":r["entry_date"],"exit_date":r["exit_date"],"horizon":r["horizon"],
            "stock_net_pct":round(stock-cost_bps/100,6),
            "benchmark_net_pct":round(bench-cost_bps/100,6),
            "excess_pct":round(stock-bench,6)})
    cohorts=[]
    for horizon in (3,5,10,15):
        sample=[r for r in rows if r["horizon"]==horizon]
        vals=[r["excess_pct"] for r in sample]
        cohorts.append({"horizon":horizon,"matched_n":len(vals),
          "missing_exact_benchmark_dates":missing[horizon],
          "mean_excess_pct":round(statistics.mean(vals),5) if vals else None,
          "median_excess_pct":round(statistics.median(vals),5) if vals else None,
          "fraction_beating_benchmark":round(sum(v>0 for v in vals)/len(vals),5) if vals else None})
    return {"cohorts":cohorts,"matched_rows":len(rows),"cost_bps_roundtrip_assumption":cost_bps,
      "timestamp_verified":False,"point_in_time_verified":False,"trade_ready":False,
      "predictive_edge_proven":False,"warning":"Descriptive comparison, not predictive strategy; no exchange/FX normalization; benchmark choice must be justified."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--benchmark-json",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--require-shards",type=int,default=20)
    p.add_argument("--cost-bps",type=float,default=20)
    args=p.parse_args()
    files=sorted(Path(args.root).rglob("descriptive_outcomes.json"))
    if len(files)!=args.require_shards: raise ValueError(f"incomplete_shards:{len(files)}/{args.require_shards}")
    outcomes=[]
    for file in files:
        obj=json.loads(file.read_text())
        if obj.get("trade_ready") is not False: raise ValueError("missing_research_only_flag")
        outcomes.extend(obj["rows"])
    b=json.loads(Path(args.benchmark_json).read_text())
    result=compare(outcomes,b["bars"],args.cost_bps)
    Path(args.output).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
