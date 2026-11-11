"""Research-only phase-rotated calendar controls; no predictive claims.

Uses all feasible fixed calendar offsets rather than a privileged start date.
Each control has the same number of nonoverlapping entries as selected signals.
"""
from dipsaus_offline_ohlcv_features import _valid
from dipsaus_offline_event_history_outcomes import evaluate_daily_event_history


def compare_calendar_phases(rows, *, horizon=10, fee_bps_each_side=10):
    selected = evaluate_daily_event_history(
        rows, horizon=horizon, fee_bps_each_side=fee_bps_each_side)
    if selected["status"] != "DESCRIPTIVE_HISTORY":
        return {"status": "DATA_BLOCKED", "reason": "invalid_history",
                "predictive_edge_proven": False, "trade_ready": False}
    count = selected["sample_count"]
    if not count:
        return {"status": "INSUFFICIENT_SIGNALS", "predictive_edge_proven": False,
                "trade_ready": False}
    phases = []
    for offset in range(horizon + 1):
        eligible = list(range(21 + offset, len(rows) - horizon, horizon + 1))
        if len(eligible) < count:
            continue
        returns, adverse = [], 0
        for i in eligible[:count]:
            entry = rows[i + 1]["open"]
            end = rows[i + horizon]["close"]
            net = 100 * (end / entry - 1) - 2 * fee_bps_each_side / 100
            returns.append(net)
            adverse += min(x["low"] for x in rows[i + 1:i + horizon + 1]) / entry - 1 <= -.03
        phases.append({"offset": offset, "count": count,
                       "mean_net_pct": round(sum(returns) / count, 5),
                       "severe_intraperiod_drawdowns": adverse})
    if not phases:
        return {"status": "DATA_BLOCKED", "reason": "insufficient_calendar_capacity",
                "predictive_edge_proven": False, "trade_ready": False}
    means = [p["mean_net_pct"] for p in phases]
    return {"status": "DESCRIPTIVE_PHASE_COMPARISON",
            "selected_count": count,
            "selected_mean_net_pct": selected["mean_terminal_net_pct"],
            "selected_severe_intraperiod_drawdowns":
                selected["severe_intraperiod_drawdown_count"],
            "calendar_phase_count": len(phases),
            "calendar_mean_of_phase_means_pct": round(sum(means) / len(means), 5),
            "calendar_min_phase_mean_pct": min(means),
            "calendar_max_phase_mean_pct": max(means),
            "calendar_phases": phases,
            "same_number_of_entries": True, "nonoverlapping_entries": True,
            "independent_holdout": False, "statistical_significance_tested": False,
            "predictive_edge_proven": False, "trade_ready": False}
