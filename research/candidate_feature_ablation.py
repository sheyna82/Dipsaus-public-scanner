"""Research-only single-feature ablation, frozen training thresholds and held-out events."""
import json, statistics
from pathlib import Path
from candidate_entry_snapshot import bars
from candidate_regime_cost_validation import RESEARCH_UNIVERSE, features, nonoverlap, MIN_TRAIN
from candidate_preentry_features import pre_entry_features
from candidate_feature_thresholds import training_median_thresholds, label, FEATURE_DIRECTIONS
from candidate_benchmark_excess import PATTERNS, HORIZON, COST_BPS
from candidate_ablation_risk_diagnostics import compare as compare_risk
from candidate_matched_count_placebo import placebo
from candidate_calendar_matched_placebo import calendar_placebo
from candidate_execution_sensitivity import execution_sensitivity, compare_liquidity_gates
from candidate_portfolio_capacity import compare_ablation_portfolios

FILTERS=("baseline",)+tuple(FEATURE_DIRECTIONS)+("all_three",)

def evaluate_ablation(stock,benchmark,pattern):
    cutoff=max(MIN_TRAIN,int(len(stock)*.65))
    training=[(i,pre_entry_features(stock,benchmark,i)) for i in range(50,cutoff)
              if features(stock,i)[pattern]]
    fitted=training_median_thresholds(training)
    if fitted["status"]!="TRAINING_ONLY_THRESHOLDS":
        return {"status":fitted["status"],"training_n":len(training),"trade_ready":False}
    indices=nonoverlap([i for i in range(cutoff,len(stock)-HORIZON)
                        if features(stock,i)[pattern]],HORIZON)
    by_day={r["timestamp"]//86400:r for r in benchmark}
    cohorts={key:[] for key in FILTERS}
    risk_cohorts={key:[] for key in FILTERS}
    execution_cohorts={key:[] for key in FILTERS}
    execution_blocked={key:0 for key in FILTERS}
    portfolio_events={key:[] for key in FILTERS}
    liquidity_pairs={key:[] for key in FILTERS}
    for i in indices:
        f=pre_entry_features(stock,benchmark,i)
        decision=label(f,fitted)
        if decision["status"]!="RESEARCH_ONLY":
            return {"status":"BLOCKED_FEATURE_ALIGNMENT","trade_ready":False}
        start=by_day.get(stock[i+1]["timestamp"]//86400)
        end=by_day.get(stock[i+HORIZON]["timestamp"]//86400)
        if not start or not end or start["open"]<=0 or stock[i+1]["open"]<=0:
            return {"status":"BLOCKED_BENCHMARK_ALIGNMENT","trade_ready":False}
        entry=stock[i+1]["open"]
        excess=100*(stock[i+HORIZON]["close"]/entry-end["close"]/start["open"])-COST_BPS/100
        mae=100*(min(x["low"] for x in stock[i+1:i+HORIZON+1])/entry-1)
        record=(excess,mae)
        risk_record={"net_return_pct":100*(stock[i+HORIZON]["close"]/entry-1)-COST_BPS/100,
                     "excess_pct":excess,"mae_pct":mae,
                     "session_day":stock[i+1]["timestamp"]//86400}
        execution=execution_sensitivity(stock,i,horizon=HORIZON,cost_bps=COST_BPS)
        liquidity_pair=compare_liquidity_gates(stock,i)
        liquidity_pairs["baseline"].append(liquidity_pair)
        def add_execution(key):
            if execution["status"]=="DESCRIPTIVE_EXECUTION_SENSITIVITY":
                execution_cohorts[key].append(execution)
            else:
                execution_blocked[key]+=1
        def add_portfolio_event(key):
            if execution["status"]=="DESCRIPTIVE_EXECUTION_SENSITIVITY":
                portfolio_events[key].append({
                    "entry_day":stock[i+1]["timestamp"]//86400,
                    "exit_day":stock[i+HORIZON]["timestamp"]//86400,
                    "net_return_pct":next(x["net_return_pct"] for x in execution["scenarios"]
                                           if x["adverse_entry_bps"]==25)})
        add_execution("baseline")
        add_portfolio_event("baseline")
        cohorts["baseline"].append(record)
        risk_cohorts["baseline"].append(risk_record)
        for key,passed in decision["passes"].items():
            if passed:
                liquidity_pairs[key].append(liquidity_pair)
                add_execution(key)
                add_portfolio_event(key)
                cohorts[key].append(record)
                risk_cohorts[key].append(risk_record)
        if all(decision["passes"].values()):
            liquidity_pairs["all_three"].append(liquidity_pair)
            add_execution("all_three")
            add_portfolio_event("all_three")
            cohorts["all_three"].append(record)
            risk_cohorts["all_three"].append(risk_record)
    def summary(records):
        return {"n":len(records),
                "median_excess_pct":round(statistics.median(x[0] for x in records),3) if records else None,
                "positive_excess_fraction":round(sum(x[0]>0 for x in records)/len(records),3) if records else None,
                "median_mae_pct":round(statistics.median(x[1] for x in records),3) if records else None,
                "worst_mae_pct":round(min(x[1] for x in records),3) if records else None}
    def execution_summary(key):
        records=execution_cohorts[key]
        scenario_bps=(0,10,25,50)
        return {"status":"DESCRIPTIVE_ONLY" if records else "INSUFFICIENT_LIQUID_EXECUTIONS",
                "trade_ready":False,"n":len(records),"blocked_n":execution_blocked[key],
                "mean_net_pct_by_entry_slippage_bps":{
                    str(bps):round(statistics.mean(next(x["net_return_pct"] for x in row["scenarios"]
                            if x["adverse_entry_bps"]==bps) for row in records),4) if records else None
                    for bps in scenario_bps}}
    def liquidity_summary(rows):
        both=sum(r["signal_gate_pass"] and r["legacy_gate_pass"] for r in rows)
        new_only=sum(r["signal_gate_pass"] and not r["legacy_gate_pass"] for r in rows)
        old_only=sum(r["legacy_gate_pass"] and not r["signal_gate_pass"] for r in rows)
        neither=len(rows)-both-new_only-old_only
        return {"total_events":len(rows), "both_pass":both,
                "point_in_time_only":new_only, "retrospective_only":old_only,
                "neither_pass":neither,
                "point_in_time_pass_n":both+new_only,
                "legacy_retrospective_pass_n":both+old_only,
                "net_cohort_change":new_only-old_only,
                "not_trade_ready":True}
    return {"status":"DESCRIPTIVE_ONLY","trade_ready":False,
            "liquidity_gate_comparison":{key:liquidity_summary(rows)
                                         for key,rows in liquidity_pairs.items()},
            "training_n":len(training),"test_baseline_n":len(indices),
            "thresholds":fitted["thresholds"],
            "cohorts":{key:summary(records) for key,records in cohorts.items()},
            "risk_diagnostics":compare_risk(risk_cohorts),
            "portfolio_events_25bps":portfolio_events,
            "execution_sensitivity":{key:execution_summary(key) for key in FILTERS},
            "matched_count_placebo":{key:placebo(risk_cohorts["baseline"], risk_cohorts[key])
                                      for key in FILTERS if key != "baseline"},
            "calendar_matched_placebo":{key:calendar_placebo(risk_cohorts["baseline"], risk_cohorts[key])
                                         for key in FILTERS if key != "baseline"}}

def main():
    output={"research_only":True,"trade_ready":False,
            "method":"SINGLE_FEATURE_ABLATION_FROZEN_TRAINING_MEDIANS",
            "horizon_sessions":HORIZON,"stock_cost_bps":COST_BPS,
            "filters":FILTERS,
            "limitations":["Correlated cross-symbol and overlapping calendar events",
                           "No inference or strategy selection on test results",
                           "Yahoo unadjusted prices; dividends, splits, FX and events not fully audited",
                           "Convenience universe; no survivorship-free validation"],
            "candidates":[]}
    try:benchmark=bars("SPY",history_range="5y")
    except Exception:benchmark=[]
    for symbol in RESEARCH_UNIVERSE:
        if "." in symbol:
            output["candidates"].append({"symbol":symbol,"status":"BLOCKED_CROSS_CURRENCY_BENCHMARK"})
            continue
        try:
            if not benchmark:raise ValueError("BENCHMARK_UNAVAILABLE")
            stock=bars(symbol,history_range="5y")
            if len(stock)<750:raise ValueError("INSUFFICIENT_HISTORY")
            output["candidates"].append({"symbol":symbol,
                "patterns":{p:evaluate_ablation(stock,benchmark,p) for p in PATTERNS}})
        except Exception as exc:
            output["candidates"].append({"symbol":symbol,"status":"DATA_BLOCKED",
                                         "error_type":type(exc).__name__})
    output["portfolio_capacity_25bps"]={p:compare_ablation_portfolios(output,pattern=p) for p in PATTERNS}
    path=Path("reports/candidate_feature_ablation.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps({"research_only":True,"candidates":len(output["candidates"])}))

if __name__=="__main__":main()
