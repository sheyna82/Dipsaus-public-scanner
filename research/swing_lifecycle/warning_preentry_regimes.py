"""Research-only pre-entry stock regimes; no optimized trading thresholds."""
import csv
import gzip
import json
from collections import defaultdict
from statistics import mean


def evaluate(cases_path, archive_path):
    with gzip.open(archive_path, "rt", encoding="utf-8") as stream:
        histories = {record["symbol"]: record["bars"]
                     for line in stream if (record := json.loads(line))}
    indexes = {ticker: {bar[0]: i for i, bar in enumerate(bars)}
               for ticker, bars in histories.items()}
    groups = defaultdict(list)
    counts = {"rows": 0, "missing_history": 0, "insufficient_lookback": 0}
    with open(cases_path, newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            counts["rows"] += 1
            ticker, entry = row["ticker"], row["entry_date"]
            idx = indexes.get(ticker, {}).get(entry)
            if idx is None:
                counts["missing_history"] += 1
                continue
            if idx < 20:
                counts["insufficient_lookback"] += 1
                continue
            prior = histories[ticker][idx - 20:idx]  # Excludes entry day.
            first, last = float(prior[0][4]), float(prior[-1][4])
            if first <= 0 or any(float(bar[4]) <= 0 for bar in prior):
                counts["missing_history"] += 1
                continue
            momentum = 100 * (last / first - 1)
            avg_range = mean(100 * (float(b[2]) - float(b[3])) / float(b[4])
                             for b in prior)
            key = (int(row["confirmation_sessions"]),
                   "positive" if momentum >= 0 else "negative",
                   "high_range" if avg_range >= 3 else "low_range")
            groups[key].append((
                float(row["return_difference_pp"]),
                float(row["candidate_mae_pct"]) - float(row["baseline_mae_pct"]),
                row["early_exit"] == "True",
            ))
    return {
        "research_only": True, "trade_ready": False,
        "independent_validation": False,
        "feature_timing": "20 sessions strictly before entry",
        "range_threshold_pct": 3, "counts": counts,
        "groups": [
            {"confirmation_sessions": rule, "trend": trend,
             "volatility": volatility, "n": len(values),
             "early_exits": sum(v[2] for v in values),
             "mean_return_difference_pp": mean(v[0] for v in values),
             "mean_mae_improvement_pp": mean(v[1] for v in values)}
            for (rule, trend, volatility), values in sorted(groups.items())
        ],
    }
