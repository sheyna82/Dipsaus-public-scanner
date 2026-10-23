"""Research-only fixed-schedule walk-forward ATR evaluation.

Split dates are supplied before observing holdout metrics. Each fold is
trained only on labels available by its split date. No optimization.
"""
from datetime import date
from research_chronological_atr_experiment import evaluate_chronological_csv


def evaluate_fixed_splits(stock_payload, benchmark_payload, *, split_dates,
                          horizon=10, threshold=0.08, embargo_seconds=0):
    if not isinstance(split_dates, (list, tuple)) or len(split_dates) < 2:
        raise ValueError("at_least_two_splits_required")
    parsed = []
    for day in split_dates:
        if not isinstance(day, str):
            raise ValueError("invalid_split_date")
        try:
            parsed.append(date.fromisoformat(day))
        except ValueError as exc:
            raise ValueError("invalid_split_date") from exc
    if len(set(parsed)) != len(parsed) or parsed != sorted(parsed):
        raise ValueError("splits_must_be_unique_and_sorted")
    folds = []
    for index, split in enumerate(split_dates):
        end = split_dates[index + 1] if index + 1 < len(split_dates) else None
        fold = evaluate_chronological_csv(
            stock_payload, benchmark_payload, split_date=split,
            horizon=horizon, threshold=threshold,
            embargo_seconds=embargo_seconds, holdout_end_date=end)
        folds.append(fold)
    # Fold holdouts are disjoint; overlapping outcome horizons still create
    # dependent observations, so do not claim independent pooled evidence.
    return {"folds": folds, "fold_count": len(folds),
            "overlapping_holdouts": False,
            "aggregate_independent_score": None,
            "independent_holdout_verified": False,
            "point_in_time_verified": False,
            "trade_ready": False}
