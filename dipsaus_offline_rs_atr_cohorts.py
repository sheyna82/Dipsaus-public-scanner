"""Descriptive, threshold-free RS/ATR cohort comparison of frozen events.

Uses median splits computed on the *same* observed sample; thus these are
post-hoc diagnostics, not a deployable strategy or out-of-sample evidence.
"""
from statistics import median
from dipsaus_offline_frozen_rs_atr import annotate_frozen_events_rs_atr


def compare_rs_atr_cohorts(stock, benchmark, *, horizon=10, min_per_cohort=10):
    result = annotate_frozen_events_rs_atr(stock, benchmark, horizon=horizon)
    if result.get("status") != "EXPLORATORY_FROZEN_RS_ATR":
        return {"status": "DATA_BLOCKED", "reason": result.get("reason", "feature_blocked"),
                "trade_ready": False}
    rows = result["rows"]
    if type(min_per_cohort) is not int or min_per_cohort < 2:
        return {"status": "DATA_BLOCKED", "reason": "invalid_minimum", "trade_ready": False}
    if len(rows) < 2 * min_per_cohort:
        return {"status": "DATA_BLOCKED", "reason": "insufficient_events",
                "events": len(rows), "required": 2 * min_per_cohort,
                "trade_ready": False}

    def metrics(items):
        n = len(items)
        return {"events": n,
                "mean_net_return_pct": round(sum(x["terminal_return_net_pct"] for x in items) / n, 5),
                "mean_adverse_excursion_pct": round(sum(x["max_adverse_excursion_pct"] for x in items) / n, 5),
                "positive_terminal_rate_pct": round(100 * sum(x["terminal_return_net_pct"] > 0 for x in items) / n, 3),
                "severe_adverse_rate_pct": round(100 * sum(x["max_adverse_excursion_pct"] <= -3 for x in items) / n, 3)}

    comparisons = {}
    for name, field in (("relative_strength", "relative_strength_20d_pct_points"),
                        ("atr", "atr_14d_pct")):
        cutoff = median(x[field] for x in rows)
        lower = [x for x in rows if x[field] <= cutoff]
        upper = [x for x in rows if x[field] > cutoff]
        if min(len(lower), len(upper)) < min_per_cohort:
            comparisons[name] = {"status": "INSUFFICIENT_COHORT",
                                 "cutoff": cutoff, "lower_events": len(lower), "upper_events": len(upper)}
        else:
            comparisons[name] = {"status": "DESCRIPTIVE_ONLY",
                                 "sample_derived_median_cutoff": round(cutoff, 6),
                                 "lower_or_equal": metrics(lower), "upper": metrics(upper)}
    return {"status": "EXPLORATORY_POSTHOC_COHORTS", "events": len(rows),
            "comparisons": comparisons, "cutoffs_pre_registered": False,
            "independent_holdout": False, "predictive_edge_proven": False,
            "trade_ready": False}
