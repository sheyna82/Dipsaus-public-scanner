"""Fixed-threshold chronological sanity test; descriptive only, not a trading signal."""
import csv
from collections import defaultdict
from statistics import median

CUTOFF = "2026-10-22"
HORIZONS = (3, 5, 10, 15)

def evaluate(path, threshold=-0.04, round_trip_cost_bps=30):
    by_symbol = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["date"] < CUTOFF:
                by_symbol[row["symbol"]].append((row["date"], float(row["close_usd"])))
    results = []
    for symbol, series in sorted(by_symbol.items()):
        series.sort()
        if len(set(d for d, _ in series)) != len(series):
            raise ValueError("duplicate_dates")
        prices = [v for _, v in series]
        if any(v <= 0 for v in prices):
            raise ValueError("nonpositive_price")
        split = len(prices) * 2 // 3
        for horizon in HORIZONS:
            for segment, start, end in (("train", 1, split), ("holdout", split, len(prices))):
                net = []
                i = start
                while i + horizon + 1 < end:
                    if prices[i] / prices[i-1] - 1 <= threshold:
                        gross = prices[i+1+horizon] / prices[i+1] - 1
                        net.append(gross - round_trip_cost_bps / 10000)
                        i += horizon + 2
                    else:
                        i += 1
                results.append(dict(symbol=symbol, segment=segment, horizon=horizon,
                    events=len(net), mean_net_pct=round(sum(net)/len(net)*100, 3) if net else None,
                    median_net_pct=round(median(net)*100, 3) if net else None,
                    round_trip_cost_bps=round_trip_cost_bps,
                    next_close_proxy=True, verified_execution=False,
                    validated_predictive_edge=False))
    return results

if __name__ == "__main__":
    import json, sys
    print(json.dumps(evaluate(sys.argv[1]), indent=2))
