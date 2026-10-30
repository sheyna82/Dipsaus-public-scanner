"""Conservative non-overlapping historical evaluation; research only."""
import json, statistics
from pathlib import Path
from candidate_entry_snapshot import SYMBOLS, bars

HORIZONS=(5,10,15)
PATTERNS=("above_ma20_below_ma50","above_both_mas","breakout_prior20","recovery_from_prior20_low_3to15pct")

def evaluate(rows,horizon,pattern):
    """Chronological non-overlapping entries; strictly prior bars for features."""
    n=len(rows)
    eligible=[]
    for i in range(50,n-horizon):
        entry=rows[i]["close"]
        previous=rows[i-20:i]
        ma20=statistics.mean(x["close"] for x in rows[i-19:i+1])
        ma50=statistics.mean(x["close"] for x in rows[i-49:i+1])
        low=min(x["low"] for x in previous)
        signal={
            "above_ma20_below_ma50": entry>ma20 and entry<ma50,
            "above_both_mas": entry>ma20 and entry>ma50,
            "breakout_prior20": entry>max(x["high"] for x in previous),
            "recovery_from_prior20_low_3to15pct": 1.03<=entry/low<=1.15
        }[pattern]
        if signal: eligible.append(i)
    def pick(indices):
        picked=[]
        next_allowed=50
        for i in indices:
            if i>=next_allowed:
                picked.append(i)
                next_allowed=i+horizon+1
        return picked
    selected=pick(eligible)
    # The control is matched to the *same calendar period*, not random lucky days.
    # Non-overlapping all-day control; descriptive, not a causal matched benchmark.
    control=pick(range(50,n-horizon))
    def stats(indices):
        if not indices: return {"n":0}
        returns=[rows[i+horizon]["close"]/rows[i]["close"]-1 for i in indices]
        adverse=[min(x["low"]/rows[i]["close"]-1 for x in rows[i+1:i+horizon+1]) for i in indices]
        return {"n":len(indices),"median_return_pct":round(100*statistics.median(returns),2),
                "positive_fraction":round(sum(x>0 for x in returns)/len(returns),3),
                "median_mae_pct":round(100*statistics.median(adverse),2),
                "worst_mae_pct":round(100*min(adverse),2)}
    return {"signal":stats(selected),"all_days_control":stats(control),
            "signal_dates_unix":[rows[i]["timestamp"] for i in selected],
            "eligible_for_inference":False,
            "limitations":["One-year window; sparse non-overlapping events",
                           "Control is not time- or regime-matched",
                           "No transaction costs, earnings controls, or out-of-sample testing"]}

def main():
    result={"research_only":True,"trade_ready":False,"method":"chronological greedy non-overlapping entry and holding windows",
            "candidates":[]}
    for symbol in SYMBOLS:
        try:
            rows=bars(symbol)
            if len(rows)<80: raise ValueError("INSUFFICIENT_BARS")
            result["candidates"].append({"symbol":symbol,"bars":len(rows),
                "horizons":{str(h):{p:evaluate(rows,h,p) for p in PATTERNS} for h in HORIZONS}})
        except Exception as exc:
            result["candidates"].append({"symbol":symbol,"status":"DATA_BLOCKED","error_type":type(exc).__name__})
    path=Path("reports/candidate_nonoverlap_validation.json")
    path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"statuses":{x["symbol"]:x.get("status","RESEARCH_ONLY") for x in result["candidates"]}}))

if __name__=="__main__":main()
