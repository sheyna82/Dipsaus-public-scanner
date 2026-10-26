"""Offline dated 5/10/15-session market-gate A/B from aligned price artifact.

Uses only closes available at decision session; future returns use next
session open and later close. Fixed equal-weight six-slot proxies, not a
continuous portfolio or independently authenticated execution.
"""
import json
import sys
import zipfile
from statistics import mean
from research_swing_short_regime_gate import assess_short_swing_regime
from research_swing_intratrade_excursion import excursion_for_trade, summarize_excursions

def run_regime_ab_archive(path, *, costs_bps=30, step=15):
    if type(step) is not int or step < 15 or type(costs_bps) not in (int, float) or not 0 <= costs_bps <= 1000:
        raise ValueError("invalid_assumptions")
    with zipfile.ZipFile(path) as z:
        coverage = json.loads(z.read("coverage.json"))
        symbols = [r["symbol"] for r in coverage["manifest"]["symbols"]]
        bars = {s: json.loads(z.read(s+".json"))["rows"] for s in symbols + ["SPY"]}
    date_sequences = {tuple(x["timestamp"] for x in v) for v in bars.values()}
    if len(date_sequences) != 1:
        raise ValueError("unaligned_panel")
    n = len(bars["SPY"])
    outcomes = []
    for horizon in (5,10,15):
        for t in range(60, n-horizon, step):
            market = assess_short_swing_regime([r["close"] for r in bars["SPY"][:t+1]])
            ranked = sorted(((bars[s][t]["close"]/bars[s][t-20]["close"]-1,s)
                             for s in symbols),reverse=True)[:6]
            if len(ranked) != 6:
                raise ValueError("incomplete_universe")
            net = mean(100*(bars[s][t+horizon]["close"]/bars[s][t+1]["open"]-1)
                       - costs_bps/100 for _,s in ranked)
            benchmark = 100*(bars["SPY"][t+horizon]["close"]/
                             bars["SPY"][t+1]["open"]-1)-costs_bps/100
            excursions = [excursion_for_trade(bars[s],t,horizon,entry_cost_bps=costs_bps) for _,s in ranked]
            accepted = market["new_entries_permitted_for_research"]
            # Caution state invests half the six equal slots; risk-off stays cash.
            exposure = {"normal":1.0,"caution":0.5,"risk_off":0.0}[market["state"]]
            outcomes.append({"horizon":horizon,"decision_timestamp":bars["SPY"][t]["timestamp"],
                             "state":market["state"],"exposure":exposure,
                             "ungated_net_pct":net,"gated_net_pct":net*exposure,
                             "benchmark_net_pct":benchmark,"accepted":accepted,
                             "mean_mae_pct":mean(x["mae_pct"] for x in excursions),
                             "worst_mae_pct":min(x["mae_pct"] for x in excursions),
                             "mean_mfe_pct":mean(x["mfe_pct"] for x in excursions)})
    summary=[]
    for horizon in (5,10,15):
        subset=[r for r in outcomes if r["horizon"]==horizon]
        summary.append({"horizon":horizon,"cohorts":len(subset),
                        "mean_ungated_net_pct":round(mean(r["ungated_net_pct"] for r in subset),4),
                        "mean_gated_net_pct":round(mean(r["gated_net_pct"] for r in subset),4),
                        "mean_benchmark_net_pct":round(mean(r["benchmark_net_pct"] for r in subset),4),
                        "mean_exposure":round(mean(r["exposure"] for r in subset),4),
                        "mean_trade_mae_pct":round(mean(r["mean_mae_pct"] for r in subset),4),
                        "worst_trade_mae_pct":round(min(r["worst_mae_pct"] for r in subset),4),
                        "mean_trade_mfe_pct":round(mean(r["mean_mfe_pct"] for r in subset),4),
                        "risk_off_cohorts":sum(r["state"]=="risk_off" for r in subset),
                        "caution_cohorts":sum(r["state"]=="caution" for r in subset)})
    return {"research_only":True,"trade_ready":False,"edge_proven":False,
            "independent_source_verified":False,"portfolio_overlap_modelled":False,
            "summary":summary,"observations":outcomes}

if __name__=="__main__":
    print(json.dumps(run_regime_ab_archive(sys.argv[1]),indent=2))
