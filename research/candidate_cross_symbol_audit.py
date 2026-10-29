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
        for c in candidates:
            if "patterns" not in c:continue
            evaluation=c["patterns"][pattern]["10"]
            metrics=evaluation["cost_scenarios"]["50"]["next_open_signals"]
            observations.append((evaluation,metrics))
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
            "trade_ready":False}
    return result

def main():
    result=audit(json.loads(SOURCE.read_text(encoding="utf-8")))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"symbols":result["universe_size"],"blocked":len(result["data_blocked"])}))

if __name__=="__main__":main()
