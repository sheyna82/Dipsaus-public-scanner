"""Frozen single-feature warning policy holdout; research-only.

Train on cases whose baseline exits predate 2026-01-01; evaluate on
2026 entries. Calendar-spaced cases are NOT actual scanner entries.
No tuning on the holdout and no order execution.
"""
import csv
import gzip
import json
from collections import defaultdict
from datetime import date
from statistics import mean

CUTOFF = "2026-01-01"
MIN_TRAIN_CASES = 30
MIN_TRAIN_EDGE_PP = 0.25


def evaluate(cases_path, archive_path):
    with gzip.open(archive_path, "rt", encoding="utf-8") as f:
        histories = {rec["symbol"]: rec["bars"]
                     for line in f if (rec := json.loads(line))}
    date_maps = {s: {bar[0]: i for i, bar in enumerate(bars)}
                 for s, bars in histories.items()}
    cases = []
    with open(cases_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["confirmation_sessions"]) != 1:
                continue
            bars = histories[row["ticker"]]
            index = date_maps[row["ticker"]]
            entry = index[row["entry_date"]]
            baseline = entry + 10
            if baseline >= len(bars):
                continue
            baseline_date = bars[baseline][0]
            early = row["early_exit"] == "True"
            group = None
            if early:
                t = index[row["exit_date"]] - 1
                if t >= 3 and float(bars[t-3][4]) > 0:
                    group = ("negative" if float(bars[t][4]) < float(bars[t-3][4])
                             else "nonnegative")
            cases.append({"entry": row["entry_date"], "baseline": baseline_date,
                          "early": early, "group": group,
                          "delta": float(row["return_difference_pp"]),
                          "mae_delta": float(row["candidate_mae_pct"]) -
                                       float(row["baseline_mae_pct"])})
    train = [r for r in cases if r["baseline"] < CUTOFF]
    test = [r for r in cases if r["entry"] >= CUTOFF]
    groups = defaultdict(list)
    for r in train:
        if r["early"] and r["group"] is not None:
            groups[r["group"]].append(r["delta"])
    policy = {k: len(v) >= MIN_TRAIN_CASES and mean(v) > MIN_TRAIN_EDGE_PP
              for k, v in groups.items()}
    def summarize(rows):
        selected = [r for r in rows if r["early"] and policy.get(r["group"], False)]
        return {"candidates": len(rows), "warning_exits": sum(r["early"] for r in rows),
                "policy_exits": len(selected),
                "mean_policy_minus_hold_pp": sum(r["delta"] for r in selected) / len(rows)
                if rows else None,
                "mean_always_warning_minus_hold_pp": sum(r["delta"] for r in rows) / len(rows)
                if rows else None,
                "mean_policy_mae_improvement_pp": sum(r["mae_delta"] for r in selected) / len(rows)
                if rows else None}
    return {"research_only": True, "trade_ready": False,
            "independent_scanner_validation": False,
            "holdout_touched_for_selection": False,
            "cutoff": CUTOFF, "min_train_cases": MIN_TRAIN_CASES,
            "min_train_edge_pp": MIN_TRAIN_EDGE_PP,
            "policy": policy,
            "training_group_counts": {k: len(v) for k, v in groups.items()},
            "training_group_means_pp": {k: mean(v) for k, v in groups.items()},
            "train": summarize(train), "test": summarize(test)}
