"""Connect frozen event signals to matched market return/risk evaluation.

The event evaluator exits at signal index + 10, whereas the generic matched
tool exits at signal index + horizon + 1. Pass horizon-1 explicitly and
verify every computed stock return against the frozen event outcome.
"""
from dipsaus_offline_event_history_outcomes import evaluate_daily_event_history
from dipsaus_offline_combined_return_risk import evaluate_matched_return_risk


def evaluate_frozen_events_against_market(stock, benchmark, *,
                                          event_horizon=10, fee_bps_each_side=10):
    if type(event_horizon) is not int or event_horizon < 2:
        return {"status": "DATA_BLOCKED", "reason": "invalid_horizon", "trade_ready": False}
    events = evaluate_daily_event_history(stock, horizon=event_horizon,
                                          fee_bps_each_side=fee_bps_each_side)
    if events.get("status") != "DESCRIPTIVE_HISTORY":
        return {"status": "DATA_BLOCKED", "reason": "invalid_event_history", "trade_ready": False}
    index = {r["date"]: i for i, r in enumerate(stock)}
    if len(index) != len(stock):
        return {"status": "DATA_BLOCKED", "reason": "duplicate_stock_dates", "trade_ready": False}
    try:
        indices = [index[r["signal_date"]] for r in events["outcomes"]]
    except (KeyError, TypeError):
        return {"status": "DATA_BLOCKED", "reason": "missing_signal_date", "trade_ready": False}
    result = evaluate_matched_return_risk(stock, benchmark, indices,
                                          horizon=event_horizon - 1,
                                          fee_bps_each_side=fee_bps_each_side)
    if result.get("status") != "EXPLORATORY_COMBINED_RETURN_RISK":
        return result
    # Exact same entry and exit must produce the same net stock outcome.
    for event, i in zip(events["outcomes"], indices):
        entry, end = stock[i + 1]["open"], stock[i + event_horizon]["close"]
        calculated = round(100 * (end / entry - 1) - 2 * fee_bps_each_side / 100, 5)
        if abs(calculated - event["terminal_return_net_pct"]) > 0.00002:
            return {"status": "DATA_BLOCKED", "reason": "event_return_mismatch", "trade_ready": False}
    return {**result, "frozen_event_rule": True,
            "event_horizon_sessions": event_horizon,
            "source_verified": False, "independent_holdout": False,
            "predictive_edge_proven": False, "trade_ready": False}
