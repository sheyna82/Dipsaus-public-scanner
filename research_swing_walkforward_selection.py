"""Select research candidates on training observations only.

Input rows are precomputed trade outcomes. This module cannot certify that
their features, fills, costs or labels are point-in-time correct.
"""
from collections import defaultdict
from datetime import date
from statistics import mean


def select_walkforward_candidate(rows, folds, *, min_train_trades=20):
    """Select by mean training return; report untouched validation separately.

    Each row: decision_date (date), candidate (str), net_return_pct (finite
    number), exit_date (date). Reject training rows whose exit extends past
    train_end and validation rows whose exit exceeds validation_end.
    No hyperparameter optimization is performed inside this module.
    """
    from math import isfinite
    if type(min_train_trades) is not int or min_train_trades < 1:
        raise ValueError("invalid_min_train_trades")
    normalized = []
    for row in rows:
        decision, exit_at = row["decision_date"], row["exit_date"]
        name, value = row["candidate"], row["net_return_pct"]
        if (type(decision) is not date or type(exit_at) is not date
                or exit_at < decision or not isinstance(name, str) or not name
                or type(value) not in (float, int) or not isfinite(value)):
            raise ValueError("invalid_trade_row")
        normalized.append((decision, exit_at, name, value))
    results = []
    for fold in folds:
        train, valid = defaultdict(list), defaultdict(list)
        for decision, exit_at, name, value in normalized:
            if fold.train_start <= decision <= fold.train_end and exit_at <= fold.train_end:
                train[name].append(value)
            if fold.validation_start <= decision <= fold.validation_end and exit_at <= fold.validation_end:
                valid[name].append(value)
        eligible = sorted(((-mean(values), name) for name, values in train.items()
                           if len(values) >= min_train_trades))
        chosen = eligible[0][1] if eligible else None
        observed = valid.get(chosen, []) if chosen else []
        results.append({
            "train_end": fold.train_end.isoformat(),
            "validation_start": fold.validation_start.isoformat(),
            "validation_end": fold.validation_end.isoformat(),
            "chosen_candidate": chosen,
            "training_trades": len(train[chosen]) if chosen else 0,
            "validation_trades": len(observed),
            "validation_mean_net_pct": round(mean(observed), 6) if observed else None,
            "selection_uses_validation": False,
            "independent_market_validation": False,
            "trade_ready": False,
        })
    return results
