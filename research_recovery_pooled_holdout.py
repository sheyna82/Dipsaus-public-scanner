"""Exploratory pooled holdout of a FIXED -4% dip rule, with a calendar baseline.

Vendor-unverified daily closes; no optimization on holdout.
Comparator is every eligible entry day in the same holdout, not an independent
randomized control. Each selected event enters on NEXT session close.
"""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

HORIZONS = (3, 5, 10, 15)

def evaluate(path, threshold=-0.04, cost_bps=30, cutoff="2026-10-22"):
    by_symbol = defaultdict(list)
    with Path(path).open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["date"] < cutoff:
                by_symbol[row["symbol"]].append((row["date"], float(row["close_usd"])))
    output = []
    for horizon in HORIZONS:
        selected, baseline, per_symbol = [], [], []
        for symbol, series in sorted(by_symbol.items()):
            series.sort()
            dates = [r[0] for r in series]
            prices = [r[1] for r in series]
            if len(set(dates)) != len(dates) or min(prices) <= 0:
                raise ValueError("invalid historical prices")
            split = len(prices)*2//3
            candidates = range(split, len(prices)-horizon-1)
            symbol_baseline = [(prices[i+1+horizon]/prices[i+1]-1)*100-cost_bps/100 for i in candidates]
            baseline.extend(symbol_baseline)
            i = split
            symbol_selected = []
            while i < len(prices)-horizon-1:
                if prices[i]/prices[i-1]-1 <= threshold:
                    result = (prices[i+1+horizon]/prices[i+1]-1)*100-cost_bps/100
                    symbol_selected.append(result)
                    selected.append(result)
                    i += horizon+2
                else:
                    i += 1
            per_symbol.append({"symbol":symbol,"selected_n":len(symbol_selected),
                "selected_mean_net_pct":round(mean(symbol_selected),3) if symbol_selected else None,
                "baseline_n":len(symbol_baseline)})
        output.append({"horizon":horizon,"selected_n":len(selected),
            "selected_mean_net_pct":round(mean(selected),3) if selected else None,
            "selected_median_net_pct":round(median(selected),3) if selected else None,
            "baseline_n":len(baseline),
            "baseline_mean_net_pct":round(mean(baseline),3) if baseline else None,
            "difference_in_means_pct_points":round(mean(selected)-mean(baseline),3) if selected and baseline else None,
            "symbols":per_symbol,"threshold_fixed_pct":threshold*100,
            "round_trip_cost_bps":cost_bps,"baseline_overlapping":True,
            "independent_test":False,"signal_timestamps_verified":False,"trade_ready":False})
    return output

if __name__ == "__main__":
    import json, sys
    print(json.dumps(evaluate(sys.argv[1]), indent=2))
