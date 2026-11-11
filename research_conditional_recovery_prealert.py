"""Exploratory conditional recovery cohorts using only pre-cutoff daily closes.

No scanner signal or tradable fill is inferred. Non-overlapping event windows
and a fixed threshold reduce, but do not eliminate, selection bias.
"""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median

CUTOFF = "2026-10-22"
THRESHOLD = -0.04
HORIZONS = (3, 5, 10, 15)

def analyze(path):
    grouped = defaultdict(list)
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["date"] < CUTOFF:
                grouped[row["symbol"]].append((row["date"], float(row["close_usd"])))
    output = []
    for symbol, series in sorted(grouped.items()):
        series.sort()
        closes = [price for _, price in series]
        for horizon in HORIZONS:
            observations = []
            eligible_baselines = []
            i = 1
            while i + horizon < len(closes):
                daily_return = closes[i] / closes[i-1] - 1
                forward = closes[i+horizon] / closes[i] - 1
                eligible_baselines.append(forward)
                if daily_return <= THRESHOLD:
                    observations.append(forward)
                    i += horizon + 1
                else:
                    i += 1
            output.append({
                "symbol": symbol, "horizon_sessions": horizon,
                "threshold_daily_drop_pct": -4.0,
                "selected_events": len(observations),
                "selected_median_forward_pct": round(median(observations)*100, 3) if observations else None,
                "selected_positive_fraction": round(sum(x > 0 for x in observations)/len(observations), 3) if observations else None,
                "baseline_candidate_days": len(eligible_baselines),
                "baseline_median_forward_pct": round(median(eligible_baselines)*100, 3) if eligible_baselines else None,
                "baseline_is_independent_control": False,
                "out_of_sample_validated": False,
                "predictive_edge_proven": False,
            })
    return output

if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python research_conditional_recovery_prealert.py <historical_closes.csv>")
    print(json.dumps(analyze(sys.argv[1]), indent=2))
