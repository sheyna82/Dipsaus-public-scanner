"""Deterministic same-history calendar baseline; diagnostic only, NOT independent holdout.

Compares technical signals with equally spaced, non-overlapping entries on
the same price series. The baseline is not randomized and does not establish
predictive superiority. Returns aggregate metrics only.
"""
from dipsaus_offline_ohlcv_features import _valid
from dipsaus_offline_event_history_outcomes import evaluate_daily_event_history


def compare_calendar_baseline(rows, *, horizon=10, fee_bps_each_side=10):
    selected = evaluate_daily_event_history(rows, horizon=horizon,
                                             fee_bps_each_side=fee_bps_each_side)
    if selected["status"] != "DESCRIPTIVE_HISTORY":
        return {"status": "DATA_BLOCKED", "reason": "invalid_history"}
    n = selected["sample_count"]
    if not n:
        return {"status": "INSUFFICIENT_SIGNALS", "selected_count": 0,
                "predictive_edge_proven": False}
    # Fixed calendar entries every horizon+1 bars starting at first eligible
    # date. No future prices are used to choose entry dates.
    eligible = list(range(21, len(rows) - horizon, horizon + 1))[:n]
    if len(eligible) != n:
        return {"status": "DATA_BLOCKED", "reason": "baseline_capacity"}
    returns = []
    severe_drawdowns = 0
    for i in eligible:
        entry = rows[i + 1]["open"]
        end = rows[i + horizon]["close"]
        net = 100 * (end / entry - 1) - 2 * fee_bps_each_side / 100
        returns.append(net)
        if min(x["low"] for x in rows[i + 1:i + horizon + 1]) / entry - 1 <= -.03:
            severe_drawdowns += 1
    return {"status": "DESCRIPTIVE_COMPARISON",
            "selected_count": n,
            "selected_mean_net_pct": selected["mean_terminal_net_pct"],
            "calendar_count": len(returns),
            "calendar_mean_net_pct": round(sum(returns) / len(returns), 5),
            "calendar_severe_intraperiod_drawdowns": severe_drawdowns,
            "selected_severe_intraperiod_drawdowns":
                selected["severe_intraperiod_drawdown_count"],
            "calendar_selection": "fixed_start_first_eligible_stride_horizon_plus_one",
            "independent_holdout": False, "statistical_significance_tested": False,
            "predictive_edge_proven": False, "trade_ready": False}
