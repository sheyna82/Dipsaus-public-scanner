"""Research-only fee/slippage sensitivity on the existing frozen event rule.

Borrowed concept: execution-cost stress testing used by backtesting engines.
This module does not fit thresholds or alter any production settings.
"""
from dipsaus_offline_event_history_outcomes import evaluate_daily_event_history


def compare_execution_costs(rows, *, horizon=10, cost_bps_each_side=(10, 25, 50)):
    if not isinstance(cost_bps_each_side, (tuple, list)) or not cost_bps_each_side:
        return {"status": "DATA_BLOCKED", "reason": "INVALID_COST_SCENARIOS"}
    if any(type(c) not in (int, float) or not 0 <= c <= 100 for c in cost_bps_each_side):
        return {"status": "DATA_BLOCKED", "reason": "INVALID_COST_SCENARIOS"}
    scenarios = []
    dates = None
    for cost in cost_bps_each_side:
        result = evaluate_daily_event_history(rows, horizon=horizon, fee_bps_each_side=cost)
        if result.get("status") != "DESCRIPTIVE_HISTORY":
            return {"status": "DATA_BLOCKED", "reason": "INVALID_HISTORY"}
        current_dates = [x["signal_date"] for x in result["outcomes"]]
        if dates is not None and current_dates != dates:
            return {"status": "DATA_BLOCKED", "reason": "SIGNAL_SET_CHANGED"}
        dates = current_dates
        scenarios.append({
            "cost_bps_each_side": cost,
            "signal_count": result["sample_count"],
            "positive_terminal_count": result["positive_terminal_count"],
            "mean_terminal_net_pct": result["mean_terminal_net_pct"],
            "severe_terminal_loss_count": result["severe_terminal_loss_count"],
            "severe_intraperiod_drawdown_count": result["severe_intraperiod_drawdown_count"],
        })
    return {"status": "DESCRIPTIVE_COST_SENSITIVITY", "scenarios": scenarios,
            "signal_dates": dates, "independent_holdout": False,
            "predictive_edge_proven": False, "trade_ready": False}
