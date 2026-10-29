"""Chronological regime-matched, cost-sensitive research. Never a trading signal."""
import json, statistics
from datetime import datetime, timezone
from pathlib import Path
from candidate_entry_snapshot import SYMBOLS, bars

# Predeclared research expansion; never selected from observed performance.
# Deliberately retain original six for comparability. Survivorship and sector
# composition biases remain; this is not an investable-universe backtest.
RESEARCH_UNIVERSE = SYMBOLS + (
    "MSFT", "GOOGL", "META", "NVDA", "INTC", "MU", "QCOM", "TXN",
    "JPM", "BAC", "XOM", "CVX", "CAT", "DE", "UNH", "PFE",
    "SAP.DE", "SIE.DE", "ASML.AS", "INGA.AS", "AIR.PA", "MC.PA",
    "SAN.MC", "IBE.MC", "NOVO-B.CO", "NESN.SW",
)

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

def summarize_next_open(rows,indices,horizon,cost_bps):
    """Signal at day i close; buy at i+1 open; exit at i+horizon close."""
    valid=[i for i in indices if i+horizon<len(rows) and
           i+1<len(rows) and rows[i+1].get("open",0)>0]
    if len(valid)!=len(indices):
        return {"n":0,"status":"BLOCKED_OPEN_PRICE_MISSING",
                "missing_open_count":len(indices)-len(valid)}
    if not indices:return {"n":0,"status":"NO_SAMPLES"}
    returns=[100*(rows[i+horizon]["close"]/rows[i+1]["open"]-1)-cost_bps/100
             for i in valid]
    adverse=[100*(min(x["low"] for x in rows[i+1:i+horizon+1])/
                  rows[i+1]["open"]-1) for i in valid]
    # Risk and capital lockup: daily close-to-entry underwater days.
    underwater_days=[sum(rows[k]["close"]<rows[i+1]["open"]
                         for k in range(i+1,i+horizon+1)) for i in valid]
    severe=[a<=-10 for a in adverse]
    return {"n":len(valid),"status":"RESEARCH_ONLY",
            "median_net_pct":round(statistics.median(returns),2),
            "positive_fraction_net":round(sum(x>0 for x in returns)/len(returns),3),
            "median_mae_pct":round(statistics.median(adverse),2),
            "worst_mae_pct":round(min(adverse),2),
            "fraction_mae_below_minus_10pct":round(sum(severe)/len(valid),3),
            "median_underwater_close_days":statistics.median(underwater_days),
            "fraction_negative_net_at_exit":round(sum(x<0 for x in returns)/len(returns),3)}

def risk_screen(metrics, matched_n):
    """Conservative research triage, not a predictive score or buy signal."""
    if metrics.get("status") != "RESEARCH_ONLY" or metrics.get("n",0)<30:
        return {"status":"INSUFFICIENT_INDEPENDENT_SIGNALS","trade_ready":False}
    if matched_n<15:
        return {"status":"INSUFFICIENT_MATCHED_CONTROLS","trade_ready":False}
    if (metrics["fraction_mae_below_minus_10pct"]>0.20 or
        metrics["worst_mae_pct"]<=-20 or
        metrics["fraction_negative_net_at_exit"]>0.45):
        return {"status":"RISK_REJECTED","trade_ready":False}
    return {"status":"FURTHER_VALIDATION_REQUIRED","trade_ready":False}


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
    matching_diagnostics={"no_eligible_same_regime_non_signal":0,
                          "blocked_by_signal_window":0,
                          "blocked_by_existing_control_window":0,
                          "matched":0}
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
    open_complete=bool(signal) and all(rows[i+1].get("open",0)>0 for i in signal+controls)
    results={"test_start_unix":rows[cutoff]["timestamp"],"signal_n":len(signal),
             "execution_model":"NEXT_SESSION_OPEN_TO_HORIZON_CLOSE" if open_complete else "SIGNAL_CLOSE_ONLY_UNEXECUTABLE_REFERENCE",
             "next_open_execution_status":"RESEARCH_ONLY" if open_complete else "BLOCKED_OPEN_PRICE_MISSING",
             "matched_control_n":len(controls),
             "matching_diagnostics":matching_diagnostics,"matched_fraction":round(len(controls)/len(signal),3) if signal else 0,
             "cost_scenarios":{},"trade_ready":False,
             "inferentially_valid":False,
             "limitations":["Test-only last 35% of available five-year window; no training/tuning performed",
                            "Controls exclude all signal windows; matching remains sparse and may not be fully balanced",
                            "No earnings/event or external benchmark controls",
                            "Next-open model uses daily open proxy, not broker-confirmed fills, spreads or slippage",
                            "Cost scenarios illustrative, not verified DEGIRO fees/FX/spread"]}
    for bps in COST_BPS:
        results["cost_scenarios"][str(bps)]={"signals":summarize(rows,signal,horizon,bps),
                                             "matched_controls":summarize(rows,controls,horizon,bps),
                                             "next_open_signals":summarize_next_open(rows,signal,horizon,bps),
                                             "next_open_matched_controls":summarize_next_open(rows,controls,horizon,bps)}
    # Preserve signal dates for cross-symbol clustering; never treat correlated
    # simultaneous events as independent statistical observations.
    results["signal_dates_utc"] = [
        datetime.fromtimestamp(rows[i]["timestamp"], timezone.utc).strftime("%Y-%m-%d") for i in signal
    ]
    results["risk_screen_50bps"] = risk_screen(
        results["cost_scenarios"]["50"]["next_open_signals"],len(controls))
    return results

def main():
    output={"research_only":True,"trade_ready":False,"horizons":list(HORIZONS),
            "cost_bps_round_trip":list(COST_BPS),"requested_history":"5y",
            "costs_are_illustrative":True,"research_universe_size":len(RESEARCH_UNIVERSE),
            "universe_selection":"PREDECLARED_CONVENIENCE_SAMPLE_NOT_SURVIVORSHIP_FREE",
            "candidates":[]}
    for symbol in RESEARCH_UNIVERSE:
        try:
            rows=bars(symbol, history_range="5y")
            if len(rows)<750:raise ValueError("INSUFFICIENT_FIVE_YEAR_BARS")
            span_days=(rows[-1]["timestamp"]-rows[0]["timestamp"])/86400
            if span_days<1200:raise ValueError("INSUFFICIENT_FIVE_YEAR_COVERAGE")
            if any(rows[i]["timestamp"]<=rows[i-1]["timestamp"] for i in range(1,len(rows))):
                raise ValueError("NON_MONOTONIC_TIMESTAMPS")
            max_gap_days=max((rows[i]["timestamp"]-rows[i-1]["timestamp"])/86400
                             for i in range(1,len(rows)))
            if max_gap_days>10:raise ValueError("EXCESSIVE_HISTORY_GAP")
            output["candidates"].append({"symbol":symbol,"bars":len(rows),
                "history_span_days":round(span_days,1),
                "max_observed_bar_gap_days":round(max_gap_days,1),
                "history_coverage_status":"FIVE_YEAR_RESEARCH_MINIMUM_MET",
                "patterns":{p:{str(h):evaluate(rows,h,p) for h in HORIZONS} for p in PATTERNS}})
        except Exception as exc:
            output["candidates"].append({"symbol":symbol,"status":"DATA_BLOCKED","error_type":type(exc).__name__})
    path=Path("reports/candidate_regime_cost_validation.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps({"status":{x["symbol"]:x.get("status","RESEARCH_ONLY") for x in output["candidates"]}}))

if __name__=="__main__":main()
