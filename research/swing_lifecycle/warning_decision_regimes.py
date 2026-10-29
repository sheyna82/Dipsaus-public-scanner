"""Decision-time warning diagnostics; research-only, never a trading rule."""
import csv
import gzip
import json
from collections import defaultdict
from statistics import mean


def evaluate(cases_path, archive_path):
    with gzip.open(archive_path, "rt", encoding="utf-8") as stream:
        histories = {record["symbol"]: record["bars"]
                     for line in stream if (record := json.loads(line))}
    dates = {ticker: {bar[0]: i for i, bar in enumerate(bars)}
             for ticker, bars in histories.items()}
    groups = defaultdict(list)
    skipped = defaultdict(int)
    with open(cases_path, newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["early_exit"] != "True":
                skipped["not_early_exit"] += 1
                continue
            ticker = row["ticker"]
            bars = histories.get(ticker)
            if bars is None:
                skipped["missing_ticker"] += 1
                continue
            entry = dates[ticker].get(row["entry_date"])
            exit_idx = dates[ticker].get(row["exit_date"])
            if entry is None or exit_idx is None or exit_idx <= entry + 1:
                skipped["bad_dates"] += 1
                continue
            t = exit_idx - 1  # Warning at close t; exit at open t+1.
            if t < 10:
                skipped["insufficient_lookback"] += 1
                continue
            close = float(bars[t][4])
            entry_open = float(bars[entry][1])
            prev_close = float(bars[t - 3][4])
            prior_range = mean(100 * (float(b[2]) - float(b[3])) / float(b[4])
                               for b in bars[t - 9:t - 4])
            recent_range = mean(100 * (float(b[2]) - float(b[3])) / float(b[4])
                                for b in bars[t - 4:t + 1])
            if min(close, entry_open, prev_close, prior_range) <= 0:
                skipped["invalid_prices"] += 1
                continue
            drawdown = 100 * (close / entry_open - 1)
            momentum3 = 100 * (close / prev_close - 1)
            expansion = recent_range / prior_range
            keys = [("all", "all"),
                    ("position_return", "negative" if drawdown < 0 else "nonnegative"),
                    ("momentum_3d", "negative" if momentum3 < 0 else "nonnegative"),
                    ("range_expansion", "increasing" if expansion > 1 else "not_increasing")]
            item = (float(row["return_difference_pp"]),
                    float(row["candidate_mae_pct"]) - float(row["baseline_mae_pct"]))
            for dimension, category in keys:
                groups[(int(row["confirmation_sessions"]), dimension, category,
                        row["entry_quarter"] != "2025-Q1")].append(item)
    return {
        "research_only": True, "independent_validation": False,
        "selection": "only early warning exits",
        "feature_cutoff": "warning close before next open",
        "skipped": dict(skipped),
        "groups": [
            {"confirmations": key[0], "dimension": key[1], "category": key[2],
             "outside_2025_q1": key[3], "n": len(values),
             "mean_return_difference_pp": mean(v[0] for v in values),
             "mean_mae_improvement_pp": mean(v[1] for v in values)}
            for key, values in sorted(groups.items())
        ],
    }
