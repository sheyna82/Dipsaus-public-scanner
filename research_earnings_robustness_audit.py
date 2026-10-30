"""Conservative descriptive robustness audit; not a strategy backtest."""
import argparse,collections,json,math,statistics
from pathlib import Path

def audit(files,cost_bps=20):
    if not 0<=cost_bps<=1000: raise ValueError("invalid_cost_bps")
    rows=[]; seen=set()
    for file in files:
        obj=json.loads(Path(file).read_text())
        if obj.get("trade_ready") is not False: raise ValueError("missing_research_only_flag")
        for r in obj["rows"]:
            key=(r["symbol"],r["event_date"],r["horizon"])
            if key in seen: raise ValueError("duplicate_event_horizon:"+str(key))
            seen.add(key)
            if r["entry_date"]<=r["event_date"] or r["exit_date"]<r["entry_date"]: raise ValueError("invalid_chronology")
            if not math.isfinite(float(r["gross_return_pct"])): raise ValueError("nonfinite_return")
            rows.append(r)
    output=[]
    for horizon in (3,5,10,15):
        group=[r for r in rows if r["horizon"]==horizon]
        gross=sorted(float(r["gross_return_pct"]) for r in group)
        if not gross: continue
        n=len(gross); trimmed=gross[n//10:n-n//10]
        net=[x-cost_bps/100 for x in gross]
        months=collections.defaultdict(list)
        for r in group: months[r["entry_date"][:7]].append(float(r["gross_return_pct"]))
        output.append({"horizon":horizon,"n":n,"distinct_symbols":len({r["symbol"] for r in group}),
          "mean_gross_pct":round(statistics.mean(gross),5),
          "median_gross_pct":round(statistics.median(gross),5),
          "trimmed_mean_gross_pct":round(statistics.mean(trimmed),5),
          "mean_net_after_assumed_cost_pct":round(statistics.mean(net),5),
          "positive_net_fraction":round(sum(x>0 for x in net)/n,5),
          "entry_month_means_gross_pct":{m:round(statistics.mean(v),5) for m,v in sorted(months.items())},
          "note":"Costs are a scenario, not verified actual fills; events unverified; overlapping observations; no benchmark."})
    return {"rows":len(rows),"cost_bps_roundtrip_assumption":cost_bps,
      "timestamp_verified":False,"trade_ready":False,"predictive_edge_proven":False,"cohorts":output}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--require-shards",type=int,default=20)
    p.add_argument("--cost-bps",type=float,default=20)
    args=p.parse_args()
    files=sorted(Path(args.root).rglob("descriptive_outcomes.json"))
    if len(files)!=args.require_shards: raise ValueError(f"incomplete_outcome_shards:{len(files)}/{args.require_shards}")
    result=audit(files,args.cost_bps)
    Path(args.output).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
