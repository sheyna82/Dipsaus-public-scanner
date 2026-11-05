"""Summarize strictly non-overlapping forward windows for a descriptive research baseline."""
from decimal import Decimal
from research_past_return_signal_baseline import evaluate_past_return_signal


def nonoverlapping_momentum_summary(stock_rows, spy_rows, *, lookback=3, horizon=3):
    evaluation = evaluate_past_return_signal(stock_rows, spy_rows, lookback=lookback, horizon=horizon)
    rows = evaluation["observations"]
    # Every horizon-th signal has a non-overlapping outcome window.
    selected = rows[::horizon]
    positive = [x for x in selected if x["signal_positive_past_excess"]]
    negative = [x for x in selected if not x["signal_positive_past_excess"]]
    def mean(group):
        if not group:
            return None
        return str(sum(Decimal(x["future_excess_percentage_points"]) for x in group) / len(group))
    return {
        "lookback": lookback, "horizon": horizon,
        "all_overlapping_observations": len(rows),
        "nonoverlapping_observations": len(selected),
        "positive_count": len(positive), "negative_count": len(negative),
        "mean_future_excess_positive_pp": mean(positive),
        "mean_future_excess_negative_pp": mean(negative),
        "small_sample": len(selected) < 30,
        "in_sample_only": True,
        "predictive_skill_established": False, "trade_ready": False}
