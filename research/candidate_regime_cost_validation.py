"""Chronological regime-matched, cost-sensitive research. Never a trading signal."""
import json, statistics
from pathlib import Path
from candidate_entry_snapshot import SYMBOLS, bars
from candidate_nonoverlap_validation import PATTERNS

HORIZONS=(5,10,15)
COST_BPS=(0,25,50,100)
MIN_TRAIN=100

def features(rows,i):
    close=rows[i]["close"]
    ma20=statistics.mean(x["close"] for x in rows[i-19:i+1])
    ma50=statistics.mean(x["close"] for x in rows[i-49:i+1])
    prev=rows[i-20:i]
    low=min(x["low"] for x in prev)
    return {
        "above_ma20_below_ma50":close>ma20 and close<ma50,
        "above_both_mas":close>ma20 and close>ma50,
        "breakout_prior20":close>max(x["high"] for x in prev),
        "recovery_from_prior20_low_3to15pct":1.03<=close/low<=1.15,
        "regime":(close>ma20,close>ma50),
    }

def nonoverlap(indices,horizon):
    chosen=[];next_free=0
    for i in sorted(indices):
        if i>=next_free:
            chosen.append(i)
            next_free=i+horizon+1
    return chosen

def summarize(rows,indices,horizon,cost_bps):
    if not indices:return {"n":0}
    returns=[100*(rows[i+horizon]["close"]/rows[i]["close"]-1)-cost_bps/100 for i in indices]
    mae=[100*(min(x["low"] for x in rows[i+1:i+horizon+1])/rows[i]["close"]-1) for i in indices]
    return {"n":len(indices),"median_net_pct":round(statistics.median(returns),2),
            "positive_fraction_net":round(sum(x>0 for x in returns)/len(returns),3),
            "median_mae_pct":round(statistics.median(mae),2),
            "worst_mae_pct":round(min(mae),2)}

def evaluate(rows,horizon,pattern,cost_bps=50):
    """Test-only last 35% of timeline; controls matched on MA20/MA50 regime.
    Historical matching uses only features known at entry. No parameter tuning."""
    cutoff=max(MIN_TRAIN,int(len(rows)*.65))
    if len(rows)-cutoff-horizon<20:
        return {"status":"INSUFFICIENT_TEST_WINDOW","trade_ready":False}
    f={i:features(rows,i) for i in range(50,len(rows)-horizon)}
    test=[i for i in range(cutoff,len(rows)-horizon)]
    signal=nonoverlap([i for i in test if f[i][pattern]],horizon)
    # Matched controls: same regime, not a signal, deterministic earliest available
    # after each signal; controls must not overlap one another.
    # Controls must be disjoint from every signal holding window and each other.
    # For MA-defined patterns a matching regime may imply the pattern itself:
    # report zero controls rather than manufacture a comparison.
    controls=[]
    signal_windows=[(i,i+horizon) for i in signal]
    for i in signal:
        candidates=[]
        for j in test:
            if j==i or f[j][pattern] or f[j]["regime"]!=f[i]["regime"] or abs(j-i)>20:
                continue
            window=(j,j+horizon)
            if any(not (window[1]<a or window[0]>b) for a,b in signal_windows):
                continue
            if any(not (window[1]<k or window[0]>k+horizon) for k in controls):
                continue
            candidates.append(j)
        if candidates:
            controls.append(min(candidates,key=lambda j:(abs(j-i),j)))
    # Do not imply pairing if controls could not be found.
    results={"test_start_unix":rows[cutoff]["timestamp"],"signal_n":len(signal),
             "execution_model":"SIGNAL_CLOSE_ONLY_UNEXECUTABLE_REFERENCE",
             "next_open_execution_status":"BLOCKED_OPEN_PRICE_MISSING",
             "matched_control_n":len(controls),"matched_fraction":round(len(controls)/len(signal),3) if signal else 0,
             "cost_scenarios":{},"trade_ready":False,
             "inferentially_valid":False,
             "limitations":["Test-only 35% of one year; no training/tuning performed",
                            "Controls exclude all signal windows; matching remains sparse and may not be fully balanced",
                            "No earnings/event or external benchmark controls",
                            "Source bars lack open prices; close-to-close results are not executable next-open backtests",
                            "Cost scenarios illustrative, not verified DEGIRO fees/FX/spread"]}
    for bps in COST_BPS:
        results["cost_scenarios"][str(bps)]={"signals":summarize(rows,signal,horizon,bps),
                                             "matched_controls":summarize(rows,controls,horizon,bps)}
    return results

def main():
    output={"research_only":True,"trade_ready":False,"horizons":list(HORIZONS),
            "cost_bps_round_trip":list(COST_BPS),"candidates":[]}
    for symbol in SYMBOLS:
        try:
            rows=bars(symbol)
            if len(rows)<150:raise ValueError("INSUFFICIENT_BARS")
            output["candidates"].append({"symbol":symbol,"bars":len(rows),
                "patterns":{p:{str(h):evaluate(rows,h,p) for h in HORIZONS} for p in PATTERNS}})
        except Exception as exc:
            output["candidates"].append({"symbol":symbol,"status":"DATA_BLOCKED","error_type":type(exc).__name__})
    path=Path("reports/candidate_regime_cost_validation.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps({"status":{x["symbol"]:x.get("status","RESEARCH_ONLY") for x in output["candidates"]}}))

if __name__=="__main__":main()
