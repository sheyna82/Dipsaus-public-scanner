"""Predeclared research-only downside evaluation metrics.

Fixed risk thresholds are evaluation labels, NOT stoploss orders.
No score tuning, trading signals, or private portfolio state.
"""


def downside_metrics(rows, *, loss_threshold_pct=-3.0):
    if not isinstance(rows, list) or not -100 < loss_threshold_pct < 0:
        return {"status": "REJECTED", "reason": "invalid_input"}
    if not rows:
        return {"status": "INSUFFICIENT", "count": 0, "trade_ready": False}
    try:
        returns = [float(r["net_return_pct"]) for r in rows]
    except (KeyError, TypeError, ValueError, OverflowError):
        return {"status": "REJECTED", "reason": "invalid_returns"}
    if any(not -1000 < x < 10000 for x in returns):
        return {"status": "REJECTED", "reason": "invalid_returns"}
    severe = [x for x in returns if x <= loss_threshold_pct]
    losses = [x for x in returns if x < 0]
    return {"status": "RESEARCH_ONLY", "count": len(returns),
            "loss_threshold_pct": loss_threshold_pct,
            "severe_loss_count": len(severe),
            "severe_loss_fraction": len(severe) / len(returns),
            "any_loss_fraction": len(losses) / len(returns),
            "average_loss_pct": sum(losses) / len(losses) if losses else None,
            "worst_exit_return_pct": min(returns),
            "note": "10-session exit outcomes; not intraperiod drawdown or stoploss instructions.",
            "trade_ready": False}
