"""Research-only forward downside diagnostics, not a stop-loss or trading signal."""
from decimal import Decimal
from research_past_return_signal_baseline import evaluate_past_return_signal


def momentum_forward_downside(stock_rows, spy_rows, *, lookback=3, horizon=3):
    """Nonoverlapping signal windows; compute worst close-to-close path after signal.

    Uses future prices ONLY for outcome labels, never for signal formation.
    """
    evaluated = evaluate_past_return_signal(stock_rows, spy_rows, lookback=lookback, horizon=horizon)
    stock = {r["date"]: Decimal(str(r["close"])) for r in stock_rows}
    spy = {r["date"]: Decimal(str(r["close"])) for r in spy_rows}
    sessions = sorted(stock.keys() & spy.keys())
    positions = {day: i for i, day in enumerate(sessions)}
    result = []
    for signal in evaluated["observations"][::horizon]:
        start = positions[signal["signal_session"]]
        initial = stock[sessions[start]]
        initial_spy = spy[sessions[start]]
        path = sessions[start + 1:start + horizon + 1]
        worst_stock = min((stock[d] / initial - 1) * 100 for d in path)
        worst_excess = min(
            ((stock[d] / initial - 1) - (spy[d] / initial_spy - 1)) * 100
            for d in path)
        result.append({"signal_session": signal["signal_session"],
                       "future_end_session": signal["future_end_session"],
                       "positive_momentum": signal["signal_positive_past_excess"],
                       "worst_forward_stock_return_pp": str(worst_stock),
                       "worst_forward_excess_pp": str(worst_excess)})
    def summarize(group):
        if not group:
            return {"count": 0, "mean_worst_stock_pp": None,
                    "mean_worst_excess_pp": None}
        return {"count": len(group),
                "mean_worst_stock_pp": str(sum(Decimal(x["worst_forward_stock_return_pp"]) for x in group) / len(group)),
                "mean_worst_excess_pp": str(sum(Decimal(x["worst_forward_excess_pp"]) for x in group) / len(group))}
    return {"method": "nonoverlapping_forward_downside",
            "positive": summarize([r for r in result if r["positive_momentum"]]),
            "negative": summarize([r for r in result if not r["positive_momentum"]]),
            "observations": result, "future_prices_used_only_as_labels": True,
            "research_only": True, "independently_verified": False,
            "predictive_skill_established": False, "trade_ready": False}


def chronological_forward_downside(stock_rows, spy_rows, *, lookback=3, horizon=3, train_fraction=0.7):
    """Evaluate downside in a chronological holdout, purging boundary-crossing labels."""
    from research_chronological_momentum_holdout import chronological_momentum_holdout
    split = chronological_momentum_holdout(stock_rows, spy_rows, lookback=lookback,
                                           horizon=horizon, train_fraction=train_fraction)
    boundary = split["holdout_start"]
    outcome = momentum_forward_downside(stock_rows, spy_rows, lookback=lookback, horizon=horizon)
    # Select non-overlapping windows separately per partition; preserve the boundary purge.
    training = [r for r in outcome["observations"] if r["future_end_session"] < boundary]
    holdout = [r for r in outcome["observations"] if r["signal_session"] >= boundary]
    def summarize(rows):
        def median(group):
            values = sorted(Decimal(r["worst_forward_stock_return_pp"]) for r in group)
            if not values:
                return None
            mid = len(values) // 2
            return str(values[mid] if len(values) % 2 else
                       (values[mid - 1] + values[mid]) / 2)
        def minimum(group):
            return str(min(Decimal(r["worst_forward_stock_return_pp"]) for r in group)) if group else None
        def mean(group, field):
            return (str(sum((Decimal(r[field]) for r in group), Decimal(0)) / len(group))
                    if group else None)
        return {"count": len(rows),
                "positive_count": sum(r["positive_momentum"] for r in rows),
                "negative_count": sum(not r["positive_momentum"] for r in rows),
                "positive_mean_worst_stock_pp": mean(
                    [r for r in rows if r["positive_momentum"]], "worst_forward_stock_return_pp"),
                "negative_mean_worst_stock_pp": mean(
                    [r for r in rows if not r["positive_momentum"]], "worst_forward_stock_return_pp"),
                "positive_median_worst_stock_pp": median(
                    [r for r in rows if r["positive_momentum"]]),
                "negative_median_worst_stock_pp": median(
                    [r for r in rows if not r["positive_momentum"]]),
                "positive_worst_single_window_pp": minimum(
                    [r for r in rows if r["positive_momentum"]]),
                "negative_worst_single_window_pp": minimum(
                    [r for r in rows if not r["positive_momentum"]]),
                "positive_windows_down_5pct": sum(
                    Decimal(r["worst_forward_stock_return_pp"]) <= -5
                    for r in rows if r["positive_momentum"]),
                "negative_windows_down_5pct": sum(
                    Decimal(r["worst_forward_stock_return_pp"]) <= -5
                    for r in rows if not r["positive_momentum"])}
    return {"method": "chronological_forward_downside_diagnostic",
            "holdout_start": boundary, "training": summarize(training),
            "holdout": summarize(holdout),
            "note": "descriptive fixed-window cohort comparison; no model fitted",
            "research_only": True, "independently_verified": False,
            "predictive_skill_established": False, "trade_ready": False}
