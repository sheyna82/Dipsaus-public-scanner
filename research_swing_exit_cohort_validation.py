"""Offline evaluation of preregistered exit policies over dated cohorts.

This is descriptive validation only, not a p-value or independent proof of
edge. Consecutive overlapping holding periods are flagged rather than counted
as independent trials. Date windows are supplied and must be source-attested.
"""
from datetime import date
from decimal import Decimal, InvalidOperation


def _date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("invalid_cohort_date") from None


def _money(value):
    if isinstance(value, bool):
        raise ValueError("invalid_net_pnl")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid_net_pnl") from None
    if not result.is_finite():
        raise ValueError("invalid_net_pnl")
    return result


def summarize_policy_cohorts(cohorts, *, expected_policies=(
        "fixed_horizon", "close_target_next_open", "close_trailing_next_open")):
    if not isinstance(cohorts, (list, tuple)) or not cohorts:
        raise ValueError("empty_cohorts")
    seen = set()
    records = []
    for item in cohorts:
        if not isinstance(item, dict):
            raise ValueError("invalid_cohort")
        cohort_id = item.get("cohort_id")
        if not isinstance(cohort_id, str) or not cohort_id or cohort_id in seen:
            raise ValueError("duplicate_or_invalid_cohort")
        seen.add(cohort_id)
        start, end = _date(item.get("entry_date")), _date(item.get("last_exit_date"))
        if end <= start:
            raise ValueError("invalid_cohort_window")
        outcomes = item.get("policies")
        if not isinstance(outcomes, dict) or set(outcomes) != set(expected_policies):
            raise ValueError("unmatched_policies")
        values = {policy: _money(outcomes[policy]) for policy in expected_policies}
        records.append((start, end, cohort_id, values))
    records.sort()
    overlaps = []
    latest_end = None
    for start, end, cohort_id, _ in records:
        if latest_end is not None and start <= latest_end:
            overlaps.append(cohort_id)
        latest_end = end if latest_end is None else max(latest_end, end)
    summaries = {}
    for policy in expected_policies:
        pnls = [row[3][policy] for row in records]
        total = sum(pnls, Decimal(0))
        summaries[policy] = {
            "cohort_count": len(pnls),
            "positive_cohort_count": sum(x > 0 for x in pnls),
            "negative_cohort_count": sum(x < 0 for x in pnls),
            "aggregate_net_pnl": str(total.quantize(Decimal("0.01"))),
            "mean_net_pnl_per_cohort": str((total / len(pnls)).quantize(Decimal("0.01"))),
        }
    return {
        "research_only": True, "predictive_edge_proven": False,
        "outcome_source_independently_verified": False,
        "cohort_count": len(records),
        "overlapping_cohort_count": len(overlaps),
        "overlapping_cohort_ids": overlaps,
        "independent_trials_established": False,
        "results": summaries,
    }
