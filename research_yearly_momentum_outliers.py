"""Descriptive outlier sensitivity for disjoint calendar-year momentum cohorts."""
from collections import defaultdict
from decimal import Decimal
from statistics import median
from research_past_return_signal_baseline import evaluate_past_return_signal


def yearly_momentum_outlier_sensitivity(stock_rows, spy_rows, *, lookback=3, horizon=3):
    if type(horizon) is not int or horizon < 1:
        raise ValueError("invalid_horizon")
    observations = evaluate_past_return_signal(
        stock_rows, spy_rows, lookback=lookback, horizon=horizon)["observations"]
    groups = defaultdict(list)
    for row in observations[::horizon]:
        groups[row["signal_session"][:4]].append(row)

    def metrics(rows):
        values = sorted(Decimal(r["future_excess_percentage_points"]) for r in rows)
        if not values:
            return {"count": 0, "mean_pp": None, "median_pp": None,
                    "mean_without_extremes_pp": None, "min_pp": None, "max_pp": None}
        trimmed = values[1:-1] if len(values) >= 5 else []
        return {"count": len(values),
                "mean_pp": str(sum(values) / len(values)),
                "median_pp": str(median(values)),
                "mean_without_extremes_pp": str(sum(trimmed) / len(trimmed)) if trimmed else None,
                "min_pp": str(values[0]), "max_pp": str(values[-1])}

    years = []
    for year in sorted(groups):
        rows = groups[year]
        years.append({"year": year,
                      "positive": metrics([r for r in rows if r["signal_positive_past_excess"]]),
                      "negative": metrics([r for r in rows if not r["signal_positive_past_excess"]])})
    return {"method": "yearly_momentum_outlier_sensitivity",
            "years": years, "trimming_rule": "remove_one_lowest_and_one_highest_per_group",
            "exploratory_not_independent_validation": True,
            "research_only": True, "trade_ready": False, "predictive_skill_established": False}
