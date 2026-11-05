"""Research-only conservative interpretation of yearly outlier sensitivity.

The count threshold is a heuristic, not a power calculation or significance test.
"""
from decimal import Decimal


def yearly_outlier_evidence_review(report, *, minimum_per_group=30):
    if type(minimum_per_group) is not int or minimum_per_group < 1:
        raise ValueError("invalid_minimum_per_group")
    results = []
    for row in report.get("results", []):
        if row.get("status") != "descriptive_only":
            results.append({"symbol": row["symbol"], "year": row["year"],
                            "status": "insufficient_data", "research_only": True})
            continue
        pos, neg = row["positive_count"], row["negative_count"]
        mean = Decimal(row["mean_difference_pp"])
        median = Decimal(row["median_difference_pp"])
        trimmed = Decimal(row["trimmed_difference_pp"])
        sign = lambda x: 1 if x > 0 else -1 if x < 0 else 0
        agreement = sign(mean) == sign(median) == sign(trimmed)
        enough = pos >= minimum_per_group and neg >= minimum_per_group
        results.append({"symbol": row["symbol"], "year": row["year"],
                        "status": "descriptive_only",
                        "positive_count": pos, "negative_count": neg,
                        "minimum_per_group": minimum_per_group,
                        "minimum_count_is_heuristic": True,
                        "group_sizes_sufficient": enough,
                        "all_three_directions_agree": agreement,
                        "interpretation": ("small_group" if not enough else
                                           "outlier_sensitive" if not agreement else
                                           "direction_consistent_descriptive_only"),
                        "predictive_skill_established": False})
    return {"research_only": True, "independent_validation": False,
            "trade_ready": False, "predictive_skill_established": False,
            "results": results}
