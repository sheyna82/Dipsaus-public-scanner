"""Descriptive cross-symbol audit; no independence or trade-readiness claims."""
import json
from collections import Counter
from pathlib import Path

SOURCE=Path("reports/candidate_regime_cost_validation.json")
OUTPUT=Path("reports/candidate_cross_symbol_audit.json")
PATTERNS=("breakout_prior20","recovery_from_prior20_low_3to15pct")

def audit(data):
    candidates=data["candidates"]
    result={"research_only":True,"trade_ready":False,
            "cross_symbol_independence_unverified":True,
            "universe_size":len(candidates),
            "data_blocked":[c["symbol"] for c in candidates if "patterns" not in c],
            "patterns":{}}
    for pattern in PATTERNS:
        observations=[]
        date_counts=Counter()
        for c in candidates:
            if "patterns" not in c:continue
            evaluation=c["patterns"][pattern]["10"]
            metrics=evaluation["cost_scenarios"]["50"]["next_open_signals"]
            observations.append((evaluation,metrics))
            date_counts.update(set(evaluation.get("signal_dates_utc",[])))
        result["patterns"][pattern]={
            "symbols_evaluated":len(observations),
            "total_nonoverlap_within_symbol_signals":sum(x["signal_n"] for x,_ in observations),
            "total_matched_controls":sum(x["matched_control_n"] for x,_ in observations),
            "positive_symbol_medians":sum(m.get("median_net_pct",float("-inf"))>0 for _,m in observations),
            "symbols_with_at_least_15_controls":sum(x["matched_control_n"]>=15 for x,_ in observations),
            "symbols_with_at_least_30_signals":sum(x["signal_n"]>=30 for x,_ in observations),
            "signals_without_matching_controls":sum(max(0,x["signal_n"]-x["matched_control_n"]) for x,_ in observations),
            "risk_status_counts":dict(Counter(x["risk_screen_50bps"]["status"] for x,_ in observations)),
            "pooled_win_rate_not_computed":"Shared dates, sectors and regimes can correlate outcomes",
            "confidence_interval_status":"NOT_ESTIMATED_CORRELATED_EVENTS",
            "distinct_signal_calendar_dates":len(date_counts),
            "dates_with_multiple_symbols_signaling":sum(n>1 for n in date_counts.values()),
            "maximum_symbols_signaling_same_day":max(date_counts.values(),default=0),
            "signal_events_on_shared_dates":sum(n for n in date_counts.values() if n>1),
            "fraction_signal_events_on_shared_dates":round(
                sum(n for n in date_counts.values() if n>1)/sum(date_counts.values()),3
            ) if date_counts else None,
            "unique_dates_as_maximum_independent_calendar_clusters":len(date_counts),
            "signal_date_coverage_status":"AVAILABLE" if all("signal_dates_utc" in x for x,_ in observations) else "INCOMPLETE",
            "trade_ready":False}
    return result

def main():
    result=audit(json.loads(SOURCE.read_text(encoding="utf-8")))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"symbols":result["universe_size"],"blocked":len(result["data_blocked"])}))

if __name__=="__main__":main()
