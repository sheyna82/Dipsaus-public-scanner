"""Research-only matched family comparison; no predictive claims or live orders.

Each observation must have an externally verified outcome and dated entry/exit.
A family is compared only within the same decision cohort and horizon.
"""
from collections import defaultdict
from datetime import date
from math import isfinite
from statistics import mean, median

def compare_signal_families(rows):
    if not isinstance(rows, (list, tuple)):
        raise ValueError("invalid_rows")
    seen = set()
    grouped = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid_row")
        key = (row.get("cohort_id"), row.get("symbol"), row.get("horizon"))
        if key in seen or any(not isinstance(x, str) or not x for x in key[:2]):
            raise ValueError("duplicate_or_invalid_observation")
        seen.add(key)
        h = key[2]
        if type(h) is not int or h not in (3, 5, 10, 20):
            raise ValueError("invalid_horizon")
        family = row.get("family")
        if not isinstance(family, str) or not family:
            raise ValueError("invalid_family")
        entry, exit_ = date.fromisoformat(row["entry_date"]), date.fromisoformat(row["exit_date"])
        if exit_ <= entry:
            raise ValueError("invalid_dates")
        if row.get("outcome_verified") is not True:
            raise ValueError("unverified_outcome")
        net = row.get("net_return_pct")
        if isinstance(net, bool) or not isinstance(net, (int, float)) or not isfinite(net):
            raise ValueError("invalid_net_return")
        grouped[(key[0], h, family)].append(float(net))
    summaries = []
    for (cohort, horizon, family), returns in sorted(grouped.items()):
        summaries.append({"cohort_id": cohort, "horizon": horizon, "family": family,
                          "count": len(returns), "mean_net_pct": mean(returns),
                          "median_net_pct": median(returns),
                          "win_fraction": sum(x > 0 for x in returns) / len(returns)})
    # Only compare families when both are observed in the same cohort/horizon.
    matched = []
    by_cohort = defaultdict(dict)
    for item in summaries:
        by_cohort[(item["cohort_id"], item["horizon"])][item["family"]] = item
    for (cohort, horizon), families in sorted(by_cohort.items()):
        labels = sorted(families)
        for i, left in enumerate(labels):
            for right in labels[i + 1:]:
                matched.append({"cohort_id": cohort, "horizon": horizon,
                                "family_a": left, "family_b": right,
                                "difference_mean_net_percentage_points":
                                    families[left]["mean_net_pct"] - families[right]["mean_net_pct"]})
    return {"research_only": True, "predictive_edge_proven": False,
            "independent_trials_established": False,
            "profitability_ranking_available": False,
            "summaries": summaries, "matched_family_differences": matched}
