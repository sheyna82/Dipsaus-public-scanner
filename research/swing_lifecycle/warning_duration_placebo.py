"""Research-only duration-matched placebo for historical warning exits.

The placebo draws exit holding durations from TRAINING-period warning exits,
using a deterministic hash of ticker and entry date. It does not inspect
future prices to choose the exit. Compare on the same eligible candidates.
No trading integration and no claim of statistical independence.
"""
import csv
import gzip
import hashlib
import json
from collections import Counter
from datetime import date

CUTOFF = "2026-01-01"


def evaluate(cases_path, archive_path, *, cutoff=CUTOFF):
    with gzip.open(archive_path, "rt", encoding="utf-8") as stream:
        histories = {r["symbol"]: r["bars"] for line in stream
                     if (r := json.loads(line))}
    indexes = {symbol: {bar[0]: i for i, bar in enumerate(bars)}
               for symbol, bars in histories.items()}
    rows = []
    with open(cases_path, newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if int(row["confirmation_sessions"]) != 1:
                continue
            symbol = row["ticker"]
            if symbol not in indexes:
                continue
            index = indexes[symbol]
            if row["entry_date"] not in index or row["exit_date"] not in index:
                continue
            start = index[row["entry_date"]]
            end = start + 10
            if end >= len(histories[symbol]):
                continue
            warning_duration = index[row["exit_date"]] - start
            if not 1 <= warning_duration <= 10:
                continue
            rows.append((row, symbol, start, end, warning_duration,
                         histories[symbol][end][0]))
    training_durations = [duration for row, _, _, _, duration, baseline_date in rows
                          if baseline_date < cutoff and row["early_exit"] == "True"
                          and duration < 10]
    if not training_durations:
        raise ValueError("no_training_warning_durations")
    durations = sorted(training_durations)
    result = []
    for row, symbol, start, end, warning_duration, _ in rows:
        if row["entry_date"] < cutoff:
            continue
        bars = histories[symbol]
        key = (symbol + "|" + row["entry_date"]).encode("utf-8")
        # Hold to day 10 when the warning policy itself would hold.
        # Thus placebo and warning exit the same number of positions early.
        selected = (durations[int.from_bytes(hashlib.sha256(key).digest()[:8], "big") % len(durations)]
                    if row["early_exit"] == "True" else 10)
        entry_open = float(bars[start][1])
        baseline_open = float(bars[end][1])
        placebo_open = float(bars[start + selected][1])
        if min(entry_open, baseline_open, placebo_open) <= 0:
            raise ValueError("invalid_open")
        lows = [entry_open] + [float(b[3]) for b in bars[start + 1:start + selected]] + [placebo_open]
        result.append({
            "ticker": symbol, "entry_date": row["entry_date"],
            "quarter": row["entry_date"][:4] + "-Q" + str((date.fromisoformat(row["entry_date"]).month - 1)//3 + 1),
            "warning_early": row["early_exit"] == "True",
            "warning_duration": warning_duration,
            "placebo_duration": selected,
            "warning_minus_hold_pp": float(row["return_difference_pp"]),
            "warning_minus_placebo_pp": float(row["return_difference_pp"]) - (placebo_open - baseline_open) / entry_open * 100,
            "placebo_minus_hold_pp": (placebo_open - baseline_open) / entry_open * 100,
            "placebo_mae_improvement_pp": (min(lows) / entry_open - 1) * 100 - float(row["baseline_mae_pct"]),
        })
    if not result:
        raise ValueError("no_out_of_sample_placebo_candidates")

    def aggregate(subset):
        n = len(subset)
        return {
            "candidates": n,
            "early_exits": sum(r["warning_early"] for r in subset),
            "warning_minus_hold_pp": sum(r["warning_minus_hold_pp"] for r in subset) / n if n else None,
            "placebo_minus_hold_pp": sum(r["placebo_minus_hold_pp"] for r in subset) / n if n else None,
            "warning_minus_placebo_pp": sum(r["warning_minus_placebo_pp"] for r in subset) / n if n else None,
        }
    return {
        "research_only": True, "trade_ready": False,
        "summary": aggregate(result),
        "by_quarter": {q: aggregate([r for r in result if r["quarter"] == q]) for q in sorted({r["quarter"] for r in result})},
        "by_ticker": {s: aggregate([r for r in result if r["ticker"] == s]) for s in sorted({r["ticker"] for r in result})},
        "placebo_selection": "sha256 ticker|entry_date, training-only duration pool",
        "training_duration_counts": dict(sorted(Counter(durations).items())),
        "test_candidates": len(result),
        "warning_early_exits": sum(r["warning_early"] for r in result),
        "placebo_early_exits": sum(r["placebo_duration"] < 10 for r in result),
        "mean_warning_minus_placebo_pp": (sum(r["warning_minus_placebo_pp"] for r in result) / len(result) if result else None),
        "rows": result,
        "limitations": [
            "Same warning-selected positions exit early; this conditional placebo does not test warning selection against random selection.",
            "Duration distributions match in aggregate, not individual positions.",
            "Placebo uses the warning flag to match exposure; paired uncertainty is still required.",
            "Equal exit counts make per-exit incremental cost cancel; absolute net returns still incur costs.",
            "Overlapping candidates and common market shocks require clustered inference.",
            "Calendar-spaced entries are not actual DIPSAUS signals."
        ],
    }
