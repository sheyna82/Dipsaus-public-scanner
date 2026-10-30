"""Chronological research-only holdout for the existing momentum baseline.

The holdout boundary is fixed by signal time, not selected by observed returns.
Training labels that reach into holdout are purged.
"""
from decimal import Decimal
from research_past_return_signal_baseline import evaluate_past_return_signal


def chronological_momentum_holdout(stock_rows, spy_rows, *, lookback=3, horizon=3, train_fraction=0.7):
    if not isinstance(train_fraction, (float, int)) or isinstance(train_fraction, bool) or not 0 < train_fraction < 1:
        raise ValueError("invalid_train_fraction")
    observations = evaluate_past_return_signal(
        stock_rows, spy_rows, lookback=lookback, horizon=horizon)["observations"]
    boundary = int(len(observations) * train_fraction)
    if boundary < horizon or len(observations) - boundary < horizon:
        raise ValueError("insufficient_holdout")
    holdout_start = observations[boundary]["signal_session"]
    training = [r for r in observations[:boundary] if r["future_end_session"] < holdout_start]
    testing = observations[boundary:]

    def summary(rows):
        # Non-overlapping forward outcome windows within each partition.
        selected = rows[::horizon]
        positive = [r for r in selected if r["signal_positive_past_excess"]]
        negative = [r for r in selected if not r["signal_positive_past_excess"]]

        def mean(group):
            if not group:
                return None
            return str(sum((Decimal(r["future_excess_percentage_points"]) for r in group), Decimal(0)) / len(group))

        return {"observations": len(selected), "positive_count": len(positive),
                "negative_count": len(negative),
                "mean_positive_excess_pp": mean(positive),
                "mean_negative_excess_pp": mean(negative)}

    return {"method": "chronological_purged_momentum_holdout",
            "holdout_start": holdout_start,
            "purged_training_observations": boundary - len(training),
            "training": summary(training), "holdout": summary(testing),
            "research_only": True, "independently_verified": False,
            "predictive_skill_established": False, "trade_ready": False}
