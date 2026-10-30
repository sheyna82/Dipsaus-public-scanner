"""Research-only uncertainty gate for chronological downside cohorts.

Do not interpret overlapping Wilson intervals as a significance test.
This deliberately conservative gate never emits a buy/sell recommendation.
"""
from research_momentum_forward_downside import chronological_forward_downside


def downside_evidence_gate(stock_rows, spy_rows, *, lookback=3, horizon=3, train_fraction=0.7,
                           minimum_per_group=30):
    if type(minimum_per_group) is not int or minimum_per_group < 1:
        raise ValueError("invalid_minimum_per_group")
    result = chronological_forward_downside(stock_rows, spy_rows, lookback=lookback,
                                             horizon=horizon, train_fraction=train_fraction)
    holdout = result["holdout"]
    pos, neg = holdout["positive_down_5pct_wilson95"], holdout["negative_down_5pct_wilson95"]
    enough = min(holdout["positive_count"], holdout["negative_count"]) >= minimum_per_group
    separated = pos is not None and neg is not None and (
        pos["upper"] < neg["lower"] or neg["upper"] < pos["lower"])
    return {
        "method": "conservative_downside_evidence_gate",
        "holdout_start": result["holdout_start"],
        "positive_count": holdout["positive_count"],
        "negative_count": holdout["negative_count"],
        "minimum_per_group": minimum_per_group,
        "additional_positive_windows_needed": max(0, minimum_per_group - holdout["positive_count"]),
        "additional_negative_windows_needed": max(0, minimum_per_group - holdout["negative_count"]),
        "sample_target_is_heuristic_not_power_analysis": True,
        "sample_size_sufficient": enough,
        "intervals_nonoverlapping": separated,
        "descriptive_evidence_sufficient": enough and separated,
        "reasons": ([]
                    if enough and separated else
                    (["insufficient_group_samples"] if not enough else []) +
                    (["overlapping_or_missing_intervals"] if not separated else [])),
        "not_a_hypothesis_test": True,
        "serial_dependence_not_adjusted": True,
        "research_only": True,
        "predictive_skill_established": False,
        "trade_ready": False,
    }
