"""Research-only risk diagnostics for frozen feature-ablation cohorts.

Consumes trade-level observations; does not select strategies or place orders.
"""
import math
import statistics

FILTERS = ("baseline", "relative_strength_20d_pct", "volume_ratio_20d", "atr_14_pct", "all_three")
THRESHOLDS = (3, 5, 10)


def summarize(records):
    """Each record contains net_return_pct, excess_pct, mae_pct and session_day."""
    if not records:
        return {"n": 0, "status": "INSUFFICIENT_OBSERVATIONS", "trade_ready": False}
    required = ("net_return_pct", "excess_pct", "mae_pct", "session_day")
    if any(any(k not in r or not isinstance(r[k], (int, float)) or
                   (k != "session_day" and not math.isfinite(r[k]))
                   for k in required) for r in records):
        raise ValueError("INVALID_TRADE_RECORD")
    n = len(records)
    maes = [r["mae_pct"] for r in records]
    returns = [r["net_return_pct"] for r in records]
    excess = [r["excess_pct"] for r in records]
    days = {r["session_day"] for r in records}
    return {
        "n": n,
        "distinct_entry_days": len(days),
        "mean_net_pct": round(statistics.mean(returns), 4),
        "median_net_pct": round(statistics.median(returns), 4),
        "win_fraction": round(sum(v > 0 for v in returns) / n, 4),
        "mean_excess_pct": round(statistics.mean(excess), 4),
        "median_excess_pct": round(statistics.median(excess), 4),
        "mean_mae_pct": round(statistics.mean(maes), 4),
        "median_mae_pct": round(statistics.median(maes), 4),
        "worst_mae_pct": round(min(maes), 4),
        "mae_breach_fraction": {str(t): round(sum(v < -t for v in maes) / n, 4)
                                for t in THRESHOLDS},
        "status": "DESCRIPTIVE_ONLY",
        "trade_ready": False,
        "limitations": ["Correlated symbols and entry days",
                        "Not an independent out-of-sample confirmation"],
    }


def compare(cohorts):
    """Do not infer statistical significance from descriptive differences."""
    if any(k not in cohorts for k in FILTERS):
        raise ValueError("MISSING_FILTER_COHORT")
    result = {k: summarize(cohorts[k]) for k in FILTERS}
    base = result["baseline"]
    for key in FILTERS[1:]:
        row = result[key]
        row["delta_mean_mae_vs_baseline_pp"] = (
            round(row["mean_mae_pct"] - base["mean_mae_pct"], 4)
            if row["n"] and base["n"] else None)
        row["delta_mean_excess_vs_baseline_pp"] = (
            round(row["mean_excess_pct"] - base["mean_excess_pct"], 4)
            if row["n"] and base["n"] else None)
    return {"research_only": True, "trade_ready": False,
            "status": "DESCRIPTIVE_ONLY_NOT_VALIDATED", "filters": result}
